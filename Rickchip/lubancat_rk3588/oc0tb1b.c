// SPDX-License-Identifier: GPL-2.0
/*
 * oc0tb1b driver
 * Copyright (C) 2024
 * V0.0X01.0X00 : initial version
 */

#include <linux/clk.h>
#include <linux/delay.h>
#include <linux/device.h>
#include <linux/gpio/consumer.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/pinctrl/consumer.h>
#include <linux/pm_runtime.h>
#include <linux/regulator/consumer.h>
#include <linux/rk-camera-module.h>
#include <linux/slab.h>
#include <linux/sysfs.h>
#include <linux/version.h>
#include <media/media-entity.h>
#include <media/v4l2-async.h>
#include <media/v4l2-ctrls.h>
#include <media/v4l2-fwnode.h>
#include <media/v4l2-subdev.h>

#define DRIVER_VERSION KERNEL_VERSION(0, 0x01, 0x00)

#ifndef V4L2_CID_DIGITAL_GAIN
#define V4L2_CID_DIGITAL_GAIN V4L2_CID_GAIN
#endif

/* 1 lane RAW10, 400x400
 * pixel_rate = link_freq * 2 * lanes / bits_per_sample
 *            = 240,000,000 * 2 * 1 / 10 = 48,000,000
 */
#define OC0TB1B_PIXEL_RATE (48000000LL)
#define MIPI_FREQ 240000000U
#define OC0TB1B_XVCLK_FREQ 24000000

#define CHIP_ID 0xc754
#define OC0TB1B_REG_CHIP_ID_H 0x300A /* SC_CMMN_A: chip_id_bk[15:8] */
#define OC0TB1B_REG_CHIP_ID_L 0x300B /* SC_CMMN_B: chip_id_bk[7:0] */

#define OC0TB1B_REG_CTRL_MODE 0x0100 /* TODO: verify */
#define OC0TB1B_MODE_SW_STANDBY 0x00
#define OC0TB1B_MODE_STREAMING 0x01

#define OC0TB1B_REG_EXPOSURE_H 0x3500 /* expo_coarse[23:16] */
#define OC0TB1B_REG_EXPOSURE_M 0x3501 /* expo_coarse[15:8] */
#define OC0TB1B_REG_EXPOSURE_L 0x3502 /* expo_coarse[7:0] */
#define OC0TB1B_EXPOSURE_MIN 1
#define OC0TB1B_EXPOSURE_STEP 1
#define OC0TB1B_EXPOSURE_MARGIN 14 /* max exposure = VTS - 14 */
#define OC0TB1B_VTS_MAX 0x7fff

#define OC0TB1B_REG_ANALOG_GAIN_H 0x3508 /* gain_coarse[3:0] */
#define OC0TB1B_REG_ANALOG_GAIN_L 0x3509 /* gain_fine[7:1] */
#define OC0TB1B_ANALOG_GAIN_MIN 0x80     /* 1x = 128 */
#define OC0TB1B_ANALOG_GAIN_MAX 0x7ff
#define OC0TB1B_ANALOG_GAIN_STEP 1
#define OC0TB1B_ANALOG_GAIN_DEFAULT 0x80

#define OC0TB1B_REG_DIGITAL_GAIN_H 0x350A /* dig_gain_coarse_b[4:0] */
#define OC0TB1B_REG_DIGITAL_GAIN_M 0x350B /* dig_gain_fine_b[9:2] */
#define OC0TB1B_REG_DIGITAL_GAIN_L                                             \
  0x350C                               /* dig_gain_fine_b[1:0] in bits 7:6     \
                                        */
#define OC0TB1B_DIGITAL_GAIN_MIN 0x400 /* 1x = 1024 */
#define OC0TB1B_DIGITAL_GAIN_MAX 0x7fff
#define OC0TB1B_DIGITAL_GAIN_STEP 1
#define OC0TB1B_DIGITAL_GAIN_DEFAULT 0x400

#define OC0TB1B_REG_TEST_PATTERN 0x5e00 /* TODO: verify */
#define OC0TB1B_TEST_PATTERN_ENABLE 0x80
#define OC0TB1B_TEST_PATTERN_DISABLE 0x00

#define OC0TB1B_REG_VTS 0x380e /* TODO: verify */

#define OC0TB1B_REG_ISP_TOP_4 0x5004       /* ISP_TOP_4: manual enable bits */
#define OC0TB1B_ISP_MAN_EXPOSURE_EN BIT(2) /* Manual exposure enable */
#define OC0TB1B_ISP_MAN_GAIN_EN BIT(1)     /* Manual camera gain enable */

#define OC0TB1B_REG_FSIN_CTRL 0x3006
#define OC0TB1B_FSIN_OUTPUT_EN BIT(1)
#define OC0TB1B_STROBE_OUTPUT_EN BIT(3)
#define OC0TB1B_REG_FSIN_OUT_SEL 0x3027
#define OC0TB1B_FSIN_OUT_SEL_REG BIT(1)
#define OC0TB1B_STROBE_OUT_SEL_REG BIT(3)

#define REG_NULL 0xFFFF

#define OC0TB1B_REG_VALUE_08BIT 1
#define OC0TB1B_REG_VALUE_16BIT 2
#define OC0TB1B_REG_VALUE_24BIT 3

#define OF_CAMERA_PINCTRL_STATE_DEFAULT "rockchip,camera_default"
#define OF_CAMERA_PINCTRL_STATE_SLEEP "rockchip,camera_sleep"

#define OC0TB1B_NAME "oc0tb1b"
#define OC0TB1B_MEDIA_BUS_FMT MEDIA_BUS_FMT_Y10_1X10

static const char *const oc0tb1b_supply_names[] = {
    "avdd",  /* Analog power */
    "dovdd", /* Digital I/O power */
    "dvdd",  /* Digital core power */
};

#define OC0TB1B_NUM_SUPPLIES ARRAY_SIZE(oc0tb1b_supply_names)

struct regval {
  u16 addr;
  u8 val;
};

struct oc0tb1b_mode {
  u32 width;
  u32 height;
  struct v4l2_fract max_fps;
  u32 hts_def;
  u32 vts_def;
  u32 exp_def;
  const struct regval *reg_list;
};

struct oc0tb1b {
  struct i2c_client *client;
  struct clk *xvclk;
  struct gpio_desc *power_gpio;
  struct gpio_desc *reset_gpio;
  struct gpio_desc *pwdn_gpio;
  struct regulator_bulk_data supplies[OC0TB1B_NUM_SUPPLIES];

  struct pinctrl *pinctrl;
  struct pinctrl_state *pins_default;
  struct pinctrl_state *pins_sleep;

  struct v4l2_subdev subdev;
  struct media_pad pad;
  struct v4l2_ctrl_handler ctrl_handler;
  struct v4l2_ctrl *exposure;
  struct v4l2_ctrl *anal_gain;
  struct v4l2_ctrl *digi_gain;
  struct v4l2_ctrl *exposure_auto;
  struct v4l2_ctrl *autogain;
  struct v4l2_ctrl *hblank;
  struct v4l2_ctrl *vblank;
  struct v4l2_ctrl *test_pattern;
  struct v4l2_ctrl *pixel_rate;
  struct v4l2_ctrl *link_freq;
  struct mutex mutex;
  bool streaming;
  const struct oc0tb1b_mode *cur_mode;
  bool power_on;
  bool is_sync_master;
  u32 module_index;
  const char *module_facing;
  const char *module_name;
  const char *len_name;
  struct rkmodule_inf module_inf;
  u32 cur_vts;
  u32 cur_exposure;
  u32 cur_gain;
};

#define to_oc0tb1b(sd) container_of(sd, struct oc0tb1b, subdev)

/*
 * 400x400 @ 240fps, 1-lane MIPI RAW10, XVCLK=24MHz
 * Register sequence from OC0TB_Full_400x400_240fps_10bit.txt (capture box
 * golden settings). Only registers listed in the txt are written to the sensor.
 */
static const struct regval oc0tb1b_global_regs[] = {
    /* Standby (delay 1ms after this is done in oc0tb1b_write_reg callers) */
    {0x0100, 0x00},
    {0x0103, 0x01},
    /* PLL */
    {0x0301, 0x69},
    {0x0305, 0xf0},
    {0x0306, 0x01},
    {0x0307, 0x00},
    {0x0326, 0x93},
    {0x0327, 0x0e},
    {0x0329, 0x01},
    {0x032f, 0x00},
    {0x0360, 0x01},
    {0x0361, 0x03},
    /* System Control */
    {0x3006, 0x04},
    {0x300d, 0x08},
    {0x3018, 0x78},
    {0x301a, 0xf0},
    {0x301c, 0x78},
    {0x3020, 0x20}, // test for strobe
    /* {0x3020, 0x00}, */
    {0x3022, 0x01},
    {0x3024, 0x00},
    {0x3037, 0xb0}, // test for strobe
    /* {0x3037, 0xb4}, */
    {0x303c, 0x02},
    {0x303d, 0x02},
    {0x3106, 0x08},
    /* Group Hold */
    {0x3216, 0x00},
    {0x3217, 0x00},
    {0x3218, 0x00},
    {0x3219, 0x55},
    /* 0x34xx */
    {0x3400, 0x0c},
    {0x3406, 0x08},
    {0x3408, 0x05},
    {0x340e, 0x70},
    {0x3410, 0x00},
    {0x3420, 0x00},
    {0x3421, 0x00},
    {0x3422, 0x80},
    {0x3423, 0x00},
    {0x3424, 0x10},
    {0x3425, 0x14},
    {0x3426, 0x51},
    /* AEC / Gain */
    {0x3500, 0x00},
    {0x3504, 0x48},
    {0x3501, 0x00},
    {0x3502, 0x40},
    {0x3506, 0x23},
    {0x3508, 0x01},
    {0x3509, 0x00},
    {0x350a, 0x01},
    {0x350b, 0x00},
    {0x350c, 0x00},
    {0x3510, 0x01},
    {0x3513, 0x01},
    {0x3516, 0x01},
    {0x3541, 0x00},
    {0x3542, 0x30},
    {0x351e, 0x00},
    {0x351f, 0x00},
    {0x3503, 0xa8},
    /* AEC Auto */
    {0x3c00, 0x78},
    {0x3c01, 0x01},
    {0x3c02, 0x0f},
    {0x3c03, 0xe0},
    {0x3c05, 0x30},
    {0x3c07, 0x18},
    {0x3c0a, 0x00},
    {0x3c0b, 0x7f},
    {0x3c17, 0x01},
    {0x3c1a, 0x06},
    /* Analog Control */
    {0x3605, 0x00},
    {0x3606, 0x80},
    {0x360b, 0x48},
    {0x360c, 0x12},
    {0x360d, 0x08},
    {0x3612, 0x01},
    {0x3620, 0x09},
    {0x3622, 0x81},
    {0x3633, 0x48},
    {0x3634, 0x48},
    {0x3635, 0x48},
    {0x363a, 0x01},
    {0x3660, 0x42},
    {0x3661, 0x07},
    {0x3662, 0x80},
    {0x366e, 0x00},
    {0x3674, 0x00},
    {0x3677, 0x3f},
    {0x367a, 0x10},
    {0x367b, 0x03},
    {0x367d, 0x12},
    {0x367e, 0x2b},
    {0x3686, 0xfe},
    {0x3687, 0x2e},
    {0x3692, 0x06},
    {0x3693, 0x07},
    {0x3694, 0x00},
    {0x369f, 0x19},
    {0x36a0, 0x0b},
    {0x36a1, 0x1f},
    {0x36a2, 0x1e},
    {0x36a3, 0x0b},
    {0x36a4, 0x61},
    {0x36a5, 0x37},
    {0x36a6, 0x1f},
    {0x36a7, 0x1f},
    /* Sensor Control */
    {0x3700, 0x09},
    {0x3701, 0x22},
    {0x3702, 0x02},
    {0x3703, 0x29},
    {0x3704, 0x1f},
    {0x3705, 0x09},
    {0x3706, 0x3e},
    {0x3707, 0x28},
    {0x370a, 0x25},
    {0x370b, 0x0a},
    {0x370d, 0x7e},
    {0x370e, 0x0b},
    {0x370f, 0x80},
    {0x3710, 0x00},
    {0x3713, 0x86},
    {0x3715, 0x03},
    {0x3716, 0x00},
    {0x3717, 0xa2},
    {0x373c, 0x0f},
    {0x373f, 0x4f},
    {0x375d, 0x35},
    {0x375f, 0x3c},
    {0x3761, 0x27},
    {0x3770, 0x36},
    {0x3778, 0x00},
    {0x377a, 0x30},
    {0x37a8, 0x00},
    {0x37a9, 0x00},
    {0x37d1, 0x0f},
    {0x37da, 0x44},
    {0x37db, 0x6b},
    {0x37dc, 0x60},
    {0x37df, 0x7d},
    {0x37e9, 0x01},
    {0x37e6, 0x82},
    {0x37e7, 0x05},
    {0x37eb, 0x01},
    /* Timing Control */
    {0x3800, 0x00},
    {0x3801, 0x00},
    {0x3802, 0x00},
    {0x3803, 0x00},
    {0x3804, 0x01},
    {0x3805, 0x9f},
    {0x3806, 0x01},
    {0x3807, 0x9f},
    {0x3808, 0x01},
    {0x3809, 0x90},
    {0x380a, 0x01},
    {0x380b, 0x90},
    {0x380c, 0x00},
    {0x380d, 0xdd},
    {0x380e, 0x02},
    {0x380f, 0x52},
    {0x3810, 0x00},
    {0x3811, 0x08},
    {0x3812, 0x00},
    {0x3813, 0x08},
    {0x3814, 0x11},
    {0x3815, 0x11},
    {0x3816, 0x02},
    {0x3817, 0x42},
    {0x3818, 0x02},
    {0x381c, 0x00},
    {0x381d, 0x00},
    {0x381e, 0x00},
    {0x381f, 0x00},
    {0x3819, 0x44},
    {0x3820, 0x40},
    {0x3821, 0x04},
    {0x3823, 0x04},
    {0x3824, 0x00},
    {0x3825, 0x00},
    {0x3826, 0x00},
    {0x3827, 0x00},
    {0x382a, 0x00},
    {0x382c, 0x08},
    {0x382d, 0x52},
    {0x382e, 0x01},
    {0x3830, 0x0f},
    {0x383e, 0x13},
    {0x3840, 0x00},
    {0x384a, 0xa2},
    {0x3858, 0x00},
    {0x3859, 0x00},
    {0x3860, 0x00},
    {0x3864, 0x12},
    {0x3861, 0x00},
    {0x3866, 0x08},
    {0x3867, 0x07},
    {0x38a0, 0x00},
    {0x38a5, 0x00},
    {0x38a6, 0x00},
    {0x38a7, 0x00},
    {0x38a8, 0x00},
    /* Strobe */
    {0x3b1e, 0x09},
    {0x3b1f, 0xff}, // extra width to strobe signal
    {0x3b20, 0xff},
    {0x3b21, 0x00},
    {0x3b22, 0x00},
    {0x3b23, 0x00},
    {0x3b24, 0x00},
    {0x3b25, 0x00},
    {0x3b26, 0x00},
    {0x3b27, 0x00},
    {0x3b28, 0x00},
    {0x3b29, 0x01},
    {0x3b2a, 0xb4},
    {0x3b2b, 0x00},
    {0x3b2c, 0x10},
    {0x3b2d, 0x05},
    {0x3b2e, 0xf2},
    {0x3b2f, 0x42},
    {0x3b31, 0x00},
    /* 0x39xx block */
    {0x3904, 0x00},
    {0x3905, 0x08},
    {0x3908, 0x92},
    {0x390a, 0xd7},
    {0x390f, 0x0e},
    {0x3910, 0xd0},
    {0x3911, 0x07},
    {0x3912, 0x80},
    {0x3913, 0x40},
    {0x3918, 0x00},
    {0x391a, 0x04},
    {0x391b, 0xfa},
    {0x391c, 0x0e},
    {0x391d, 0xd0},
    {0x391f, 0x08},
    {0x3920, 0x00},
    {0x3921, 0x00},
    {0x3924, 0x12},
    {0x3925, 0x00},
    {0x3926, 0x02},
    {0x3927, 0x00},
    {0x3928, 0x8d},
    {0x3929, 0x04},
    {0x392a, 0x7e},
    {0x392b, 0x0e},
    {0x392c, 0xaa},
    {0x392f, 0x02},
    {0x3931, 0x04},
    {0x3932, 0x00},
    {0x3933, 0x12},
    {0x3936, 0x0e},
    {0x3937, 0xaa},
    {0x393a, 0x0f},
    {0x393b, 0x6c},
    {0x3941, 0x86},
    {0x3943, 0xdb},
    {0x3949, 0x30},
    {0x394b, 0xb0},
    {0x394f, 0x00},
    {0x3951, 0x97},
    {0x3953, 0xf2},
    {0x3954, 0x07},
    {0x3955, 0xe0},
    {0x3956, 0x0a},
    {0x3957, 0x42},
    {0x3959, 0x97},
    {0x395b, 0xf2},
    {0x395c, 0x0b},
    {0x395d, 0xe4},
    {0x395e, 0x0e},
    {0x395f, 0x39},
    {0x3960, 0x04},
    {0x3961, 0x9c},
    {0x3962, 0x0e},
    {0x3963, 0x98},
    {0x3966, 0x03},
    {0x3967, 0x13},
    {0x3968, 0x00},
    {0x396a, 0x0e},
    {0x396b, 0xb0},
    {0x396e, 0x0a},
    {0x396f, 0x93},
    {0x3970, 0x0b},
    {0x3971, 0xcd},
    {0x3972, 0x0a},
    {0x3973, 0xb3},
    {0x3974, 0x0b},
    {0x3975, 0xad},
    {0x3976, 0x04},
    {0x3977, 0x60},
    {0x3978, 0x0a},
    {0x3979, 0x93},
    {0x397a, 0x0e},
    {0x397b, 0x98},
    {0x397d, 0xff},
    {0x397e, 0x38},
    /* 0x3axx block */
    {0x3a06, 0x08},
    {0x3a07, 0x10},
    {0x3a08, 0x0a},
    {0x3a09, 0x93},
    {0x3a0a, 0x0c},
    {0x3a0b, 0x1d},
    {0x3a0c, 0x0e},
    {0x3a0d, 0x98},
    {0x3a0e, 0x04},
    {0x3a0f, 0x60},
    {0x3a10, 0x0e},
    {0x3a11, 0xd0},
    {0x3a12, 0x04},
    {0x3a13, 0x60},
    {0x3a14, 0x0e},
    {0x3a15, 0xd0},
    {0x3a17, 0x0b},
    {0x3a18, 0x28},
    {0x3a19, 0x0c},
    {0x3a1a, 0x00},
    {0x3a1b, 0x0b},
    {0x3a1c, 0xf3},
    {0x3a1d, 0x0b},
    {0x3a1e, 0x7d},
    {0x3a1f, 0x0b},
    {0x3a20, 0xe7},
    {0x3a21, 0x0b},
    {0x3a22, 0x95},
    {0x3a23, 0x0a},
    {0x3a24, 0xb3},
    {0x3a25, 0x0b},
    {0x3a26, 0x9d},
    {0x3a28, 0x0b},
    {0x3a29, 0xad},
    {0x3a2a, 0x0b},
    {0x3a2b, 0xbd},
    {0x3a2c, 0x0b},
    {0x3a2d, 0xcd},
    {0x3a2e, 0x0a},
    {0x3a2f, 0x93},
    {0x3a30, 0x0c},
    {0x3a31, 0x00},
    {0x3a32, 0x0a},
    {0x3a33, 0x96},
    {0x3a39, 0x0a},
    {0x3a3a, 0x46},
    {0x3a3b, 0x0a},
    {0x3a3c, 0x93},
    {0x3a3d, 0x0e},
    {0x3a3e, 0x3d},
    {0x3a3f, 0x0e},
    {0x3a40, 0x98},
    {0x3a41, 0x0a},
    {0x3a42, 0x42},
    {0x3a43, 0x0a},
    {0x3a44, 0xac},
    {0x3a45, 0x0e},
    {0x3a46, 0x39},
    {0x3a47, 0x0e},
    {0x3a48, 0xaa},
    {0x3a49, 0xb3},
    {0x3a4a, 0x0a},
    {0x3a4b, 0xad},
    {0x3a4c, 0x0b},
    {0x3a4d, 0x93},
    {0x3a4e, 0x0a},
    {0x3a4f, 0xcd},
    {0x3a50, 0x0b},
    {0x3a52, 0x00},
    {0x3a53, 0x01},
    {0x3a54, 0x0f},
    {0x3a55, 0x78},
    {0x3a58, 0x18},
    {0x3a59, 0x08},
    {0x3a5a, 0xb3},
    {0x3a5b, 0x0a},
    {0x3a5c, 0xad},
    {0x3a5d, 0x0b},
    {0x3a5e, 0x93},
    {0x3a5f, 0x0a},
    {0x3a60, 0xcd},
    {0x3a61, 0x0b},
    {0x3a6a, 0x30},
    {0x3a6b, 0x00},
    {0x3a6c, 0x41},
    {0x3a6d, 0x01},
    {0x3a6e, 0x30},
    {0x3a6f, 0x00},
    {0x3a70, 0xb0},
    {0x3a71, 0x01},
    {0x3a72, 0x30},
    {0x3a73, 0x00},
    {0x3a74, 0x41},
    {0x3a75, 0x01},
    {0x3a76, 0x30},
    {0x3a77, 0x00},
    {0x3a78, 0xb0},
    {0x3a79, 0x01},
    {0x3a7a, 0xaa},
    {0x3a7b, 0xa0},
    {0x3a7c, 0x00},
    {0x3a85, 0x88},
    /* OTP_SC */
    {0x3d8c, 0x70},
    {0x3d8d, 0x5d},
    /* SENSOR_REG1 */
    {0x3f31, 0x07},
    {0x3f32, 0xe0},
    {0x3f33, 0xc4},
    /* WINDOW */
    {0x428e, 0x02},
    /* FORMAT */
    {0x4300, 0xff},
    /* SYNC_FIFO */
    {0x4580, 0x09},
    /* SPI */
    {0x4700, 0xf8},
    {0x4701, 0x44},
    {0x4702, 0x01},
    {0x4703, 0x00},
    /* MIPI_CORE */
    {0x4800, 0x64},
    {0x4802, 0x00},
    {0x4805, 0x00},
    {0x4813, 0x00},
    {0x481b, 0x3c},
    {0x481f, 0x26},
    {0x4837, 0x10},
    {0x484b, 0x27},
    {0x4860, 0x00},
    {0x4861, 0xec},
    {0x4862, 0x00},
    {0x4863, 0x00},
    /* MIPI_PHY */
    {0x4883, 0x00},
    {0x4884, 0x08},
    {0x4888, 0x90},
    {0x488b, 0x01},
    {0x488c, 0x00},
    {0x488e, 0x00},
    /* BLC */
    {0x4000, 0xf3},
    {0x4001, 0x6c},
    {0x4003, 0x40},
    {0x4008, 0x04},
    {0x4009, 0x0b},
    {0x4040, 0x04},
    {0x4041, 0x0b},
    {0x4043, 0x52},
    {0x4045, 0x52},
    {0x4047, 0x52},
    {0x4049, 0x52},
    /* FORMAT extra */
    {0x430b, 0x03},
    {0x430c, 0xff},
    {0x430d, 0x00},
    {0x430e, 0x00},
    /* SYNC_FIFO extra */
    {0x4509, 0x00},
    {0x450b, 0x83},
    /* VFIFO */
    {0x4604, 0x48},
    /* ISP_TOP */
    {0x5000, 0x17},
    {0x5001, 0x00},
    {0x5002, 0x3f},
    {0x5007, 0x01},
    {0x500a, 0x00},
    /* PRE_ISP */
    {0x5101, 0x00},
    /* OTP_DPC */
    {0x5180, 0x70},
    {0x5181, 0x14},
    {0x5182, 0x70},
    {0x5183, 0x53},
    /* 25MHz PLL overrides — NOT applicable for 24MHz XVCLK (ECS-2520MVLC-240)
     * Enable these only if XVCLK = 25MHz */
    // {0x0303, 0x03},
    // {0x0305, 0xc0},
    // {0x0323, 0x03},
    // {0x0325, 0xc0},
    /* DPC fix for small spot light */
    {0x3840, 0x40},
    {0x5282, 0x63},
    /* NOTE: streaming is started by s_stream, not here */

    {REG_NULL, 0x00},
};

/* 120fps: VTS = 0x04A4 (1188 lines) */
static const struct regval oc0tb1b_400x400_120fps_regs[] = {
    {0x380e, 0x04},
    {0x380f, 0xa4},
    {REG_NULL, 0x00},
};

/* 240fps: VTS = 0x0252 (594 lines) */
static const struct regval oc0tb1b_400x400_240fps_regs[] = {
    {0x380e, 0x02},
    {0x380f, 0x52},
    {REG_NULL, 0x00},
};

static const struct oc0tb1b_mode supported_modes[] = {
    /* [0] 120fps — default */
    {
        .width = 400,
        .height = 400,
        .max_fps =
            {
                .numerator = 10000,
                .denominator = 1200000, /* 120fps */
            },
        .hts_def = 0x00dd, /* HTS from register 0x380c/0x380d */
        .vts_def = 0x04a4, /* VTS for 120fps */
        .exp_def = 0x0080,
        .reg_list = oc0tb1b_400x400_120fps_regs,
    },
    /* [1] 240fps */
    {
        .width = 400,
        .height = 400,
        .max_fps =
            {
                .numerator = 10000,
                .denominator = 2400000, /* 240fps */
            },
        .hts_def = 0x00dd,
        .vts_def = 0x0252, /* VTS for 240fps */
        .exp_def = 0x0080,
        .reg_list = oc0tb1b_400x400_240fps_regs,
    },
};

static const s64 link_freq_menu_items[] = {
    MIPI_FREQ,
};

static const char *const oc0tb1b_test_pattern_menu[] = {
    "Disabled",
    "Vertical Color Bar Type 1",
};

/* --------------- I2C helpers --------------- */

static int oc0tb1b_write_reg(struct i2c_client *client, u16 reg, u32 len,
                             u32 val) {
  u32 buf_i, val_i;
  u8 buf[6];
  u8 *val_p;
  __be32 val_be;

  if (len > 4)
    return -EINVAL;

  buf[0] = reg >> 8;
  buf[1] = reg & 0xff;

  val_be = cpu_to_be32(val);
  val_p = (u8 *)&val_be;
  buf_i = 2;
  val_i = 4 - len;

  while (val_i < 4)
    buf[buf_i++] = val_p[val_i++];

  if (i2c_master_send(client, buf, len + 2) != (int)(len + 2))
    return -EIO;

  return 0;
}

static int oc0tb1b_write_array(struct i2c_client *client,
                               const struct regval *regs) {
  int ret = 0;

  while (regs->addr != REG_NULL) {
    ret = oc0tb1b_write_reg(client, regs->addr, OC0TB1B_REG_VALUE_08BIT,
                            regs->val);
    if (ret)
      return ret;
    regs++;
  }
  return 0;
}

static int oc0tb1b_read_reg(struct i2c_client *client, u16 reg, u32 len,
                            u32 *val) {
  struct i2c_msg msgs[2];
  u8 *data_be_p;
  __be32 data_be = 0;
  __be16 reg_addr_be = cpu_to_be16(reg);
  int ret;

  if (len > 4 || !len)
    return -EINVAL;

  data_be_p = (u8 *)&data_be;

  msgs[0].addr = client->addr;
  msgs[0].flags = 0;
  msgs[0].len = 2;
  msgs[0].buf = (u8 *)&reg_addr_be;

  msgs[1].addr = client->addr;
  msgs[1].flags = I2C_M_RD;
  msgs[1].len = len;
  msgs[1].buf = &data_be_p[4 - len];

  ret = i2c_transfer(client->adapter, msgs, ARRAY_SIZE(msgs));
  if (ret != ARRAY_SIZE(msgs))
    return -EIO;

  *val = be32_to_cpu(data_be);
  return 0;
}

/* --------------- V4L2 controls --------------- */

static int oc0tb1b_set_ctrl(struct v4l2_ctrl *ctrl) {
  struct oc0tb1b *oc0tb1b =
      container_of(ctrl->handler, struct oc0tb1b, ctrl_handler);
  struct i2c_client *client = oc0tb1b->client;
  s32 val = ctrl->val;
  int ret = 0;

  /* Controls only take effect while streaming */
  if (!pm_runtime_get_if_in_use(&client->dev))
    return 0;

  switch (ctrl->id) {
  case V4L2_CID_EXPOSURE_AUTO: {
    u32 isp_top4;

    /* V4L2_EXPOSURE_AUTO=0 → auto, V4L2_EXPOSURE_MANUAL=1 → manual */
    ret = oc0tb1b_read_reg(client, OC0TB1B_REG_ISP_TOP_4,
                           OC0TB1B_REG_VALUE_08BIT, &isp_top4);
    if (!ret) {
      if (val == V4L2_EXPOSURE_MANUAL)
        isp_top4 |= OC0TB1B_ISP_MAN_EXPOSURE_EN;
      else
        isp_top4 &= ~OC0TB1B_ISP_MAN_EXPOSURE_EN;
      ret = oc0tb1b_write_reg(client, OC0TB1B_REG_ISP_TOP_4,
                              OC0TB1B_REG_VALUE_08BIT, isp_top4);
    }
    break;
  }
  case V4L2_CID_AUTOGAIN: {
    u32 isp_top4;

    /* val=1 → auto gain, val=0 → manual gain */
    ret = oc0tb1b_read_reg(client, OC0TB1B_REG_ISP_TOP_4,
                           OC0TB1B_REG_VALUE_08BIT, &isp_top4);
    if (!ret) {
      if (val)
        isp_top4 &= ~OC0TB1B_ISP_MAN_GAIN_EN;
      else
        isp_top4 |= OC0TB1B_ISP_MAN_GAIN_EN;
      ret = oc0tb1b_write_reg(client, OC0TB1B_REG_ISP_TOP_4,
                              OC0TB1B_REG_VALUE_08BIT, isp_top4);
    }
    break;
  }
  case V4L2_CID_EXPOSURE:
    /* expo_coarse is 24-bit across 0x3500/0x3501/0x3502 */
    ret = oc0tb1b_write_reg(client, OC0TB1B_REG_EXPOSURE_H,
                            OC0TB1B_REG_VALUE_08BIT, (val >> 16) & 0xff);
    ret |= oc0tb1b_write_reg(client, OC0TB1B_REG_EXPOSURE_M,
                             OC0TB1B_REG_VALUE_08BIT, (val >> 8) & 0xff);
    ret |= oc0tb1b_write_reg(client, OC0TB1B_REG_EXPOSURE_L,
                             OC0TB1B_REG_VALUE_08BIT, val & 0xff);
    oc0tb1b->cur_exposure = val;
    break;
  case V4L2_CID_ANALOGUE_GAIN:
    /* val = 128 is 1x gain. coarse in 0x3508[3:0], fine in 0x3509[7:1] */
    ret = oc0tb1b_write_reg(client, OC0TB1B_REG_ANALOG_GAIN_H,
                            OC0TB1B_REG_VALUE_08BIT, (val >> 7) & 0x0f);
    ret |= oc0tb1b_write_reg(client, OC0TB1B_REG_ANALOG_GAIN_L,
                             OC0TB1B_REG_VALUE_08BIT, (val & 0x7f) << 1);
    oc0tb1b->cur_gain = val;
    break;
  case V4L2_CID_DIGITAL_GAIN:
    /* val = 1024 is 1x gain. coarse in 0x350A[4:0], fine in 0x350B[7:0] and
     * 0x350C[7:6] */
    ret = oc0tb1b_write_reg(client, OC0TB1B_REG_DIGITAL_GAIN_H,
                            OC0TB1B_REG_VALUE_08BIT, (val >> 10) & 0x1f);
    ret |= oc0tb1b_write_reg(client, OC0TB1B_REG_DIGITAL_GAIN_M,
                             OC0TB1B_REG_VALUE_08BIT, (val >> 2) & 0xff);
    ret |= oc0tb1b_write_reg(client, OC0TB1B_REG_DIGITAL_GAIN_L,
                             OC0TB1B_REG_VALUE_08BIT, (val & 0x03) << 6);
    break;
  default:
    dev_warn(&client->dev, "%s: ctrl(id:0x%x) not handled\n", __func__,
             ctrl->id);
    ret = -EINVAL;
    break;
  }

  pm_runtime_put(&client->dev);
  return ret;
}

static const struct v4l2_ctrl_ops oc0tb1b_ctrl_ops = {
    .s_ctrl = oc0tb1b_set_ctrl,
};

/* --------------- Power --------------- */

static int __oc0tb1b_power_on(struct oc0tb1b *oc0tb1b) {
  int ret;
  struct device *dev = &oc0tb1b->client->dev;

  if (!IS_ERR_OR_NULL(oc0tb1b->pins_default)) {
    ret = pinctrl_select_state(oc0tb1b->pinctrl, oc0tb1b->pins_default);
    if (ret < 0)
      dev_err(dev, "could not set pins\n");
  }

  ret = clk_set_rate(oc0tb1b->xvclk, OC0TB1B_XVCLK_FREQ);
  if (ret < 0)
    dev_warn(dev, "Failed to set xvclk rate (24MHz)\n");
  if (clk_get_rate(oc0tb1b->xvclk) != OC0TB1B_XVCLK_FREQ)
    dev_warn(dev, "xvclk mismatched, modes are based on 24MHz\n");
  ret = clk_prepare_enable(oc0tb1b->xvclk);
  if (ret < 0) {
    dev_err(dev, "Failed to enable xvclk\n");
    return ret;
  }

  if (!IS_ERR(oc0tb1b->reset_gpio))
    gpiod_set_value_cansleep(oc0tb1b->reset_gpio, 0);

  ret = regulator_bulk_enable(OC0TB1B_NUM_SUPPLIES, oc0tb1b->supplies);
  if (ret < 0) {
    dev_err(dev, "Failed to enable regulators\n");
    goto disable_clk;
  }

  if (!IS_ERR(oc0tb1b->reset_gpio)) {
    gpiod_set_value_cansleep(oc0tb1b->reset_gpio, 1);
    usleep_range(1000, 1200);
    gpiod_set_value_cansleep(oc0tb1b->reset_gpio, 0);
    usleep_range(1000, 1200);
  }

  if (!IS_ERR(oc0tb1b->pwdn_gpio)) {
    gpiod_set_value_cansleep(oc0tb1b->pwdn_gpio, 1);
    usleep_range(1000, 1200);
  }

  usleep_range(4000, 5000);
  oc0tb1b->power_on = true;
  return 0;

disable_clk:
  clk_disable_unprepare(oc0tb1b->xvclk);
  return ret;
}

static void __oc0tb1b_power_off(struct oc0tb1b *oc0tb1b) {
  struct device *dev = &oc0tb1b->client->dev;
  int ret;

  if (!IS_ERR(oc0tb1b->pwdn_gpio))
    gpiod_set_value_cansleep(oc0tb1b->pwdn_gpio, 0);

  clk_disable_unprepare(oc0tb1b->xvclk);

  if (!IS_ERR(oc0tb1b->reset_gpio))
    gpiod_set_value_cansleep(oc0tb1b->reset_gpio, 0);

  if (!IS_ERR_OR_NULL(oc0tb1b->pins_sleep)) {
    ret = pinctrl_select_state(oc0tb1b->pinctrl, oc0tb1b->pins_sleep);
    if (ret < 0)
      dev_dbg(dev, "could not set pins\n");
  }

  regulator_bulk_disable(OC0TB1B_NUM_SUPPLIES, oc0tb1b->supplies);
  oc0tb1b->power_on = false;
}

static int oc0tb1b_runtime_resume(struct device *dev) {
  struct i2c_client *client = to_i2c_client(dev);
  struct v4l2_subdev *sd = i2c_get_clientdata(client);
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);

  return __oc0tb1b_power_on(oc0tb1b);
}

static int oc0tb1b_runtime_suspend(struct device *dev) {
  struct i2c_client *client = to_i2c_client(dev);
  struct v4l2_subdev *sd = i2c_get_clientdata(client);
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);

  __oc0tb1b_power_off(oc0tb1b);
  return 0;
}

/* --------------- V4L2 subdev ops --------------- */

static int oc0tb1b_s_power(struct v4l2_subdev *sd, int on) {
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);
  struct i2c_client *client = oc0tb1b->client;
  int ret = 0;

  mutex_lock(&oc0tb1b->mutex);

  if (oc0tb1b->power_on == !!on)
    goto unlock_and_return;

  if (on) {
    ret = pm_runtime_get_sync(&client->dev);
    if (ret < 0) {
      pm_runtime_put_noidle(&client->dev);
      goto unlock_and_return;
    }

    ret = oc0tb1b_write_array(oc0tb1b->client, oc0tb1b_global_regs);
    if (ret) {
      v4l2_err(sd, "could not set init registers\n");
      pm_runtime_put_noidle(&client->dev);
      goto unlock_and_return;
    }

    oc0tb1b->power_on = true;
  } else {
    pm_runtime_put(&client->dev);
    oc0tb1b->power_on = false;
  }

unlock_and_return:
  mutex_unlock(&oc0tb1b->mutex);
  return ret;
}

static int oc0tb1b_s_stream(struct v4l2_subdev *sd, int on) {
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);
  struct i2c_client *client = oc0tb1b->client;
  int ret = 0;

  mutex_lock(&oc0tb1b->mutex);
  on = !!on;
  if (on == oc0tb1b->streaming)
    goto unlock;

  if (on) {
    ret = pm_runtime_get_sync(&client->dev);
    if (ret < 0) {
      pm_runtime_put_noidle(&client->dev);
      goto unlock;
    }
    ret = oc0tb1b_write_array(client, oc0tb1b->cur_mode->reg_list);
    if (ret)
      goto err_rpm_put;

    /* Configure FSIN synchronization */
    if (oc0tb1b->is_sync_master) {
      u32 val;
      /* Master: FSIN as output, STROBE as output */
      if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_CTRL,
                            OC0TB1B_REG_VALUE_08BIT, &val))
        oc0tb1b_write_reg(
            client, OC0TB1B_REG_FSIN_CTRL, OC0TB1B_REG_VALUE_08BIT,
            val | OC0TB1B_FSIN_OUTPUT_EN | OC0TB1B_STROBE_OUTPUT_EN);
      /* Output selection: normal data path for both FSIN and STROBE */
      if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_OUT_SEL,
                            OC0TB1B_REG_VALUE_08BIT, &val))
        oc0tb1b_write_reg(
            client, OC0TB1B_REG_FSIN_OUT_SEL, OC0TB1B_REG_VALUE_08BIT,
            val & ~OC0TB1B_FSIN_OUT_SEL_REG & ~OC0TB1B_STROBE_OUT_SEL_REG);
    } else {
      u32 val;
      /* Slave: FSIN as input, STROBE as output (normal data path) */
      if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_CTRL,
                            OC0TB1B_REG_VALUE_08BIT, &val))
        oc0tb1b_write_reg(
            client, OC0TB1B_REG_FSIN_CTRL, OC0TB1B_REG_VALUE_08BIT,
            (val & ~OC0TB1B_FSIN_OUTPUT_EN) | OC0TB1B_STROBE_OUTPUT_EN);
      /* STROBE output: normal data path */
      if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_OUT_SEL,
                            OC0TB1B_REG_VALUE_08BIT, &val))
        oc0tb1b_write_reg(client, OC0TB1B_REG_FSIN_OUT_SEL,
                          OC0TB1B_REG_VALUE_08BIT,
                          val & ~OC0TB1B_STROBE_OUT_SEL_REG);
    }

    ret = oc0tb1b_write_reg(client, OC0TB1B_REG_CTRL_MODE,
                            OC0TB1B_REG_VALUE_08BIT, OC0TB1B_MODE_STREAMING);
    if (ret)
      goto err_rpm_put;
  } else {
    oc0tb1b_write_reg(client, OC0TB1B_REG_CTRL_MODE, OC0TB1B_REG_VALUE_08BIT,
                      OC0TB1B_MODE_SW_STANDBY);
    pm_runtime_put(&client->dev);
  }

  oc0tb1b->streaming = on;
  goto unlock;

err_rpm_put:
  pm_runtime_put(&client->dev);
unlock:
  mutex_unlock(&oc0tb1b->mutex);
  return ret;
}

static int oc0tb1b_g_frame_interval(struct v4l2_subdev *sd,
                                    struct v4l2_subdev_frame_interval *fi) {
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);
  const struct oc0tb1b_mode *mode = oc0tb1b->cur_mode;

  fi->interval = mode->max_fps;
  return 0;
}

static int oc0tb1b_s_frame_interval(struct v4l2_subdev *sd,
                                    struct v4l2_subdev_frame_interval *fi) {
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);
  int i, best = 0;
  u32 req_fps;

  if (fi->interval.numerator == 0)
    return -EINVAL;

  /* Calculate requested fps (integer approximation) */
  req_fps = fi->interval.denominator / fi->interval.numerator;

  mutex_lock(&oc0tb1b->mutex);

  /* Find closest matching mode by fps */
  for (i = 0; i < (int)ARRAY_SIZE(supported_modes); i++) {
    u32 mode_fps = supported_modes[i].max_fps.denominator /
                   supported_modes[i].max_fps.numerator;
    u32 best_fps = supported_modes[best].max_fps.denominator /
                   supported_modes[best].max_fps.numerator;
    if (abs((int)req_fps - (int)mode_fps) < abs((int)req_fps - (int)best_fps))
      best = i;
  }

  oc0tb1b->cur_mode = &supported_modes[best];
  fi->interval = oc0tb1b->cur_mode->max_fps;

  mutex_unlock(&oc0tb1b->mutex);
  return 0;
}

static int oc0tb1b_enum_mbus_code(struct v4l2_subdev *sd,
                                  struct v4l2_subdev_state *sd_state,
                                  struct v4l2_subdev_mbus_code_enum *code) {
  if (code->index != 0)
    return -EINVAL;
  code->code = OC0TB1B_MEDIA_BUS_FMT;
  return 0;
}

static int oc0tb1b_enum_frame_sizes(struct v4l2_subdev *sd,
                                    struct v4l2_subdev_state *sd_state,
                                    struct v4l2_subdev_frame_size_enum *fse) {
  if (fse->index >= ARRAY_SIZE(supported_modes))
    return -EINVAL;
  if (fse->code != OC0TB1B_MEDIA_BUS_FMT)
    return -EINVAL;
  fse->min_width = supported_modes[fse->index].width;
  fse->max_width = supported_modes[fse->index].width;
  fse->min_height = supported_modes[fse->index].height;
  fse->max_height = supported_modes[fse->index].height;
  return 0;
}

static int oc0tb1b_get_fmt(struct v4l2_subdev *sd,
                           struct v4l2_subdev_state *sd_state,
                           struct v4l2_subdev_format *fmt) {
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);
  const struct oc0tb1b_mode *mode = oc0tb1b->cur_mode;

  mutex_lock(&oc0tb1b->mutex);
  if (fmt->which == V4L2_SUBDEV_FORMAT_TRY) {
#ifdef CONFIG_VIDEO_V4L2_SUBDEV_API
    fmt->format = *v4l2_subdev_get_try_format(sd, sd_state, fmt->pad);
#else
    mutex_unlock(&oc0tb1b->mutex);
    return -EINVAL;
#endif
  } else {
    fmt->format.width = mode->width;
    fmt->format.height = mode->height;
    fmt->format.code = OC0TB1B_MEDIA_BUS_FMT;
    fmt->format.field = V4L2_FIELD_NONE;
    fmt->format.colorspace = V4L2_COLORSPACE_RAW;
  }
  mutex_unlock(&oc0tb1b->mutex);
  return 0;
}

static int oc0tb1b_set_fmt(struct v4l2_subdev *sd,
                           struct v4l2_subdev_state *sd_state,
                           struct v4l2_subdev_format *fmt) {
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);
  const struct oc0tb1b_mode *mode;
  int i;

  mutex_lock(&oc0tb1b->mutex);

  /* Resolution is fixed at 400x400; find matching mode by size */
  mode = &supported_modes[0];
  for (i = 0; i < (int)ARRAY_SIZE(supported_modes); i++) {
    if (supported_modes[i].width == fmt->format.width &&
        supported_modes[i].height == fmt->format.height) {
      mode = &supported_modes[i];
      break;
    }
  }

  fmt->format.width = mode->width;
  fmt->format.height = mode->height;
  fmt->format.code = OC0TB1B_MEDIA_BUS_FMT;
  fmt->format.field = V4L2_FIELD_NONE;
  fmt->format.colorspace = V4L2_COLORSPACE_RAW;

  if (fmt->which == V4L2_SUBDEV_FORMAT_TRY) {
#ifdef CONFIG_VIDEO_V4L2_SUBDEV_API
    *v4l2_subdev_get_try_format(sd, sd_state, fmt->pad) = fmt->format;
#endif
  } else {
    oc0tb1b->cur_mode = mode;
    oc0tb1b->cur_vts = mode->vts_def;
  }
  mutex_unlock(&oc0tb1b->mutex);
  return 0;
}

static int
oc0tb1b_enum_frame_interval(struct v4l2_subdev *sd,
                            struct v4l2_subdev_state *sd_state,
                            struct v4l2_subdev_frame_interval_enum *fie) {
  if (fie->index >= ARRAY_SIZE(supported_modes))
    return -EINVAL;
  fie->code = OC0TB1B_MEDIA_BUS_FMT;
  fie->width = supported_modes[fie->index].width;
  fie->height = supported_modes[fie->index].height;
  fie->interval = supported_modes[fie->index].max_fps;
  return 0;
}

static int oc0tb1b_g_mbus_config(struct v4l2_subdev *sd, unsigned int pad,
                                 struct v4l2_mbus_config *config) {
  config->type = V4L2_MBUS_CSI2_DPHY;
  config->bus.mipi_csi2.num_data_lanes = 1;
  return 0;
}

static long oc0tb1b_ioctl(struct v4l2_subdev *sd, unsigned int cmd, void *arg) {
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);
  struct rkmodule_hdr_cfg *hdr;
  struct rkmodule_channel_info *ch_info;
  struct rkmodule_exp_delay *exp_delay;
  struct rkmodule_exp_info *exp_info;
  u32 stream;
  long ret = 0;

  switch (cmd) {
  case RKMODULE_GET_MODULE_INFO:
    memcpy(arg, &oc0tb1b->module_inf, sizeof(oc0tb1b->module_inf));
    break;
  case RKMODULE_GET_HDR_CFG:
    hdr = (struct rkmodule_hdr_cfg *)arg;
    hdr->esp.mode = HDR_NORMAL_VC;
    hdr->hdr_mode = NO_HDR;
    break;
  case RKMODULE_SET_QUICK_STREAM:
    stream = *((u32 *)arg);
    if (stream)
      ret = oc0tb1b_write_reg(oc0tb1b->client, OC0TB1B_REG_CTRL_MODE,
                              OC0TB1B_REG_VALUE_08BIT, OC0TB1B_MODE_STREAMING);
    else
      ret = oc0tb1b_write_reg(oc0tb1b->client, OC0TB1B_REG_CTRL_MODE,
                              OC0TB1B_REG_VALUE_08BIT, OC0TB1B_MODE_SW_STANDBY);
    break;
  case RKMODULE_GET_CHANNEL_INFO:
    ch_info = (struct rkmodule_channel_info *)arg;
    ch_info->vc = 0;
    ch_info->width = oc0tb1b->cur_mode->width;
    ch_info->height = oc0tb1b->cur_mode->height;
    ch_info->bus_fmt = OC0TB1B_MEDIA_BUS_FMT;
    break;
  case RKMODULE_GET_EXP_DELAY:
    exp_delay = (struct rkmodule_exp_delay *)arg;
    exp_delay->exp_delay = 2;
    exp_delay->gain_delay = 2;
    exp_delay->vts_delay = 1;
    break;
  case RKMODULE_GET_EXP_INFO:
    exp_info = (struct rkmodule_exp_info *)arg;
    exp_info->exp[0] = oc0tb1b->cur_exposure;
    exp_info->gain[0] = oc0tb1b->cur_gain;
    exp_info->hts = oc0tb1b->cur_mode->hts_def;
    exp_info->vts = oc0tb1b->cur_vts;
    exp_info->pclk = OC0TB1B_PIXEL_RATE;
    exp_info->gain_mode.gain_mode = RKMODULE_GAIN_MODE_LINEAR;
    exp_info->gain_mode.factor = 128;
    break;
  case RKMODULE_GET_CSI_DPHY_PARAM:
    /* oc0tb1b is single-lane non-HDR, no special dphy param needed */
    ret = -EINVAL;
    break;
  default:
    ret = -ENOIOCTLCMD;
    break;
  }
  return ret;
}

#ifdef CONFIG_COMPAT
static long oc0tb1b_compat_ioctl32(struct v4l2_subdev *sd, unsigned int cmd,
                                   unsigned long arg) {
  void __user *up = compat_ptr(arg);
  struct rkmodule_inf *inf;
  long ret = 0;

  switch (cmd) {
  case RKMODULE_GET_MODULE_INFO:
  case RKMODULE_GET_HDR_CFG:
  case RKMODULE_SET_QUICK_STREAM:
  case RKMODULE_GET_CHANNEL_INFO:
  case RKMODULE_GET_EXP_DELAY:
  case RKMODULE_GET_EXP_INFO:
  case RKMODULE_GET_CSI_DPHY_PARAM:
    inf = kzalloc(sizeof(*inf), GFP_KERNEL);
    if (!inf)
      return -ENOMEM;
    ret = oc0tb1b_ioctl(sd, cmd, inf);
    if (!ret && copy_to_user(up, inf, sizeof(*inf)))
      ret = -EFAULT;
    kfree(inf);
    break;
  default:
    ret = -ENOIOCTLCMD;
    break;
  }
  return ret;
}
#endif

/* --------------- ops tables --------------- */

static const struct dev_pm_ops oc0tb1b_pm_ops = {
    SET_RUNTIME_PM_OPS(oc0tb1b_runtime_suspend, oc0tb1b_runtime_resume, NULL)};

static const struct v4l2_subdev_core_ops oc0tb1b_core_ops = {
    .s_power = oc0tb1b_s_power,
    .ioctl = oc0tb1b_ioctl,
#ifdef CONFIG_COMPAT
    .compat_ioctl32 = oc0tb1b_compat_ioctl32,
#endif
};

static const struct v4l2_subdev_video_ops oc0tb1b_video_ops = {
    .s_stream = oc0tb1b_s_stream,
    .g_frame_interval = oc0tb1b_g_frame_interval,
    .s_frame_interval = oc0tb1b_s_frame_interval,
};

static const struct v4l2_subdev_pad_ops oc0tb1b_pad_ops = {
    .enum_mbus_code = oc0tb1b_enum_mbus_code,
    .enum_frame_size = oc0tb1b_enum_frame_sizes,
    .enum_frame_interval = oc0tb1b_enum_frame_interval,
    .get_fmt = oc0tb1b_get_fmt,
    .set_fmt = oc0tb1b_set_fmt,
    .get_mbus_config = oc0tb1b_g_mbus_config,
};

static const struct v4l2_subdev_ops oc0tb1b_subdev_ops = {
    .core = &oc0tb1b_core_ops,
    .video = &oc0tb1b_video_ops,
    .pad = &oc0tb1b_pad_ops,
};

/* --------------- probe / remove --------------- */

static int oc0tb1b_check_sensor_id(struct oc0tb1b *oc0tb1b,
                                   struct i2c_client *client) {
  struct device *dev = &client->dev;
  u32 hi = 0, lo = 0;
  int ret;

  ret = oc0tb1b_read_reg(client, OC0TB1B_REG_CHIP_ID_H, OC0TB1B_REG_VALUE_08BIT,
                         &hi);
  ret |= oc0tb1b_read_reg(client, OC0TB1B_REG_CHIP_ID_L,
                          OC0TB1B_REG_VALUE_08BIT, &lo);
  if (ret) {
    dev_err(dev, "Failed to read chip ID\n");
    return ret;
  }

  if (((hi << 8) | lo) != CHIP_ID) {
    dev_err(dev, "Unexpected sensor id(%04x), read id(%04x)\n", CHIP_ID,
            (hi << 8) | lo);
    return -ENODEV;
  }

  dev_info(dev, "Detected OC0TB1B sensor\n");

  return 0;
}

static int oc0tb1b_configure_regulators(struct oc0tb1b *oc0tb1b) {
  int i;

  for (i = 0; i < OC0TB1B_NUM_SUPPLIES; i++)
    oc0tb1b->supplies[i].supply = oc0tb1b_supply_names[i];

  return devm_regulator_bulk_get(&oc0tb1b->client->dev, OC0TB1B_NUM_SUPPLIES,
                                 oc0tb1b->supplies);
}

static int oc0tb1b_probe(struct i2c_client *client,
                         const struct i2c_device_id *id) {
  struct device *dev = &client->dev;
  struct device_node *node = dev->of_node;
  struct oc0tb1b *oc0tb1b;
  struct v4l2_subdev *sd;
  char facing[2];
  int ret;

  oc0tb1b = devm_kzalloc(dev, sizeof(*oc0tb1b), GFP_KERNEL);
  if (!oc0tb1b)
    return -ENOMEM;

  oc0tb1b->client = client;
  oc0tb1b->cur_mode = &supported_modes[0];

  oc0tb1b->xvclk = devm_clk_get(dev, "xvclk");
  if (IS_ERR(oc0tb1b->xvclk)) {
    dev_err(dev, "Failed to get xvclk\n");
    return PTR_ERR(oc0tb1b->xvclk);
  }

  oc0tb1b->reset_gpio = devm_gpiod_get_optional(dev, "reset", GPIOD_OUT_LOW);
  if (IS_ERR(oc0tb1b->reset_gpio))
    dev_warn(dev, "Failed to get reset-gpios\n");

  oc0tb1b->pwdn_gpio = devm_gpiod_get_optional(dev, "pwdn", GPIOD_OUT_LOW);
  if (IS_ERR(oc0tb1b->pwdn_gpio))
    dev_warn(dev, "Failed to get pwdn-gpios\n");

  oc0tb1b->pinctrl = devm_pinctrl_get(dev);
  if (!IS_ERR(oc0tb1b->pinctrl)) {
    oc0tb1b->pins_default =
        pinctrl_lookup_state(oc0tb1b->pinctrl, OF_CAMERA_PINCTRL_STATE_DEFAULT);
    oc0tb1b->pins_sleep =
        pinctrl_lookup_state(oc0tb1b->pinctrl, OF_CAMERA_PINCTRL_STATE_SLEEP);
  }

  oc0tb1b->is_sync_master = of_property_read_bool(node, "rockchip,sync-master");

  ret = oc0tb1b_configure_regulators(oc0tb1b);
  if (ret) {
    dev_err(dev, "Failed to get power regulators\n");
    return ret;
  }

  ret = of_property_read_u32(node, RKMODULE_CAMERA_MODULE_INDEX,
                             &oc0tb1b->module_index);
  ret |= of_property_read_string(node, RKMODULE_CAMERA_MODULE_FACING,
                                 &oc0tb1b->module_facing);
  ret |= of_property_read_string(node, RKMODULE_CAMERA_MODULE_NAME,
                                 &oc0tb1b->module_name);
  ret |= of_property_read_string(node, RKMODULE_CAMERA_LENS_NAME,
                                 &oc0tb1b->len_name);
  if (ret) {
    dev_err(dev, "could not get module information\n");
    return ret;
  }

  /* Populate module_inf for RKMODULE_GET_MODULE_INFO ioctl */
  memset(&oc0tb1b->module_inf, 0, sizeof(oc0tb1b->module_inf));
  strlcpy(oc0tb1b->module_inf.base.sensor, OC0TB1B_NAME,
          sizeof(oc0tb1b->module_inf.base.sensor));
  strlcpy(oc0tb1b->module_inf.base.module, oc0tb1b->module_name,
          sizeof(oc0tb1b->module_inf.base.module));
  strlcpy(oc0tb1b->module_inf.base.lens, oc0tb1b->len_name,
          sizeof(oc0tb1b->module_inf.base.lens));

  mutex_init(&oc0tb1b->mutex);

  sd = &oc0tb1b->subdev;
  v4l2_i2c_subdev_init(sd, client, &oc0tb1b_subdev_ops);
  ret = v4l2_ctrl_handler_init(&oc0tb1b->ctrl_handler, 12);
  if (ret)
    goto err_destroy_mutex;

  /* Pixel rate — required by rockchip-csi2-dphy */
  oc0tb1b->pixel_rate =
      v4l2_ctrl_new_std(&oc0tb1b->ctrl_handler, NULL, V4L2_CID_PIXEL_RATE, 0,
                        OC0TB1B_PIXEL_RATE, 1, OC0TB1B_PIXEL_RATE);

  /* Link frequency — required by rockchip-csi2-dphy */
  oc0tb1b->link_freq = v4l2_ctrl_new_int_menu(
      &oc0tb1b->ctrl_handler, NULL, V4L2_CID_LINK_FREQ,
      ARRAY_SIZE(link_freq_menu_items) - 1, 0, link_freq_menu_items);
  if (oc0tb1b->link_freq)
    oc0tb1b->link_freq->flags |= V4L2_CTRL_FLAG_READ_ONLY;

  /* HBlank */
  {
    u32 hblank_val = oc0tb1b->cur_mode->hts_def > oc0tb1b->cur_mode->width
                         ? oc0tb1b->cur_mode->hts_def - oc0tb1b->cur_mode->width
                         : 0;
    oc0tb1b->hblank =
        v4l2_ctrl_new_std(&oc0tb1b->ctrl_handler, NULL, V4L2_CID_HBLANK, 0,
                          0xffff, 1, hblank_val);
    if (oc0tb1b->hblank)
      oc0tb1b->hblank->flags |= V4L2_CTRL_FLAG_READ_ONLY;
  }

  /* VBlank */
  oc0tb1b->vblank =
      v4l2_ctrl_new_std(&oc0tb1b->ctrl_handler, NULL, V4L2_CID_VBLANK, 0,
                        OC0TB1B_VTS_MAX - oc0tb1b->cur_mode->height, 1,
                        oc0tb1b->cur_mode->vts_def - oc0tb1b->cur_mode->height);
  if (oc0tb1b->vblank)
    oc0tb1b->vblank->flags |= V4L2_CTRL_FLAG_READ_ONLY;

  /* Auto/Manual exposure mode: default = auto */
  oc0tb1b->exposure_auto = v4l2_ctrl_new_std_menu(
      &oc0tb1b->ctrl_handler, &oc0tb1b_ctrl_ops, V4L2_CID_EXPOSURE_AUTO,
      V4L2_EXPOSURE_MANUAL, 0, V4L2_EXPOSURE_AUTO);

  /* Auto/Manual gain: default = auto (1) */
  oc0tb1b->autogain = v4l2_ctrl_new_std(
      &oc0tb1b->ctrl_handler, &oc0tb1b_ctrl_ops, V4L2_CID_AUTOGAIN, 0, 1, 1, 1);

  /* Exposure control: range [1 .. VTS-14], default = cur_mode->exp_def */
  oc0tb1b->exposure =
      v4l2_ctrl_new_std(&oc0tb1b->ctrl_handler, &oc0tb1b_ctrl_ops,
                        V4L2_CID_EXPOSURE, OC0TB1B_EXPOSURE_MIN,
                        oc0tb1b->cur_mode->vts_def - OC0TB1B_EXPOSURE_MARGIN,
                        OC0TB1B_EXPOSURE_STEP, oc0tb1b->cur_mode->exp_def);

  /* Analog gain control */
  oc0tb1b->anal_gain = v4l2_ctrl_new_std(
      &oc0tb1b->ctrl_handler, &oc0tb1b_ctrl_ops, V4L2_CID_ANALOGUE_GAIN,
      OC0TB1B_ANALOG_GAIN_MIN, OC0TB1B_ANALOG_GAIN_MAX,
      OC0TB1B_ANALOG_GAIN_STEP, OC0TB1B_ANALOG_GAIN_DEFAULT);

  /* Digital gain control */
  oc0tb1b->digi_gain = v4l2_ctrl_new_std(
      &oc0tb1b->ctrl_handler, &oc0tb1b_ctrl_ops, V4L2_CID_DIGITAL_GAIN,
      OC0TB1B_DIGITAL_GAIN_MIN, OC0TB1B_DIGITAL_GAIN_MAX,
      OC0TB1B_DIGITAL_GAIN_STEP, OC0TB1B_DIGITAL_GAIN_DEFAULT);

  if (oc0tb1b->ctrl_handler.error) {
    ret = oc0tb1b->ctrl_handler.error;
    dev_err(dev, "Failed to init controls: %d\n", ret);
    goto err_free_handler;
  }

  sd->ctrl_handler = &oc0tb1b->ctrl_handler;

  ret = __oc0tb1b_power_on(oc0tb1b);
  if (ret)
    goto err_free_handler;

  ret = oc0tb1b_check_sensor_id(oc0tb1b, client);
  if (ret)
    goto err_power_off;
  /* Configure FSIN synchronization */
  if (oc0tb1b->is_sync_master) {
    u32 val;
    if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_CTRL,
                          OC0TB1B_REG_VALUE_08BIT, &val))
      oc0tb1b_write_reg(client, OC0TB1B_REG_FSIN_CTRL, OC0TB1B_REG_VALUE_08BIT,
                        val | OC0TB1B_FSIN_OUTPUT_EN |
                            OC0TB1B_STROBE_OUTPUT_EN);
    if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_OUT_SEL,
                          OC0TB1B_REG_VALUE_08BIT, &val))
      oc0tb1b_write_reg(
          client, OC0TB1B_REG_FSIN_OUT_SEL, OC0TB1B_REG_VALUE_08BIT,
          val & ~OC0TB1B_FSIN_OUT_SEL_REG & ~OC0TB1B_STROBE_OUT_SEL_REG);
  } else {
    u32 val;
    if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_CTRL,
                          OC0TB1B_REG_VALUE_08BIT, &val))
      oc0tb1b_write_reg(client, OC0TB1B_REG_FSIN_CTRL, OC0TB1B_REG_VALUE_08BIT,
                        (val & ~OC0TB1B_FSIN_OUTPUT_EN) |
                            OC0TB1B_STROBE_OUTPUT_EN);
    if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_OUT_SEL,
                          OC0TB1B_REG_VALUE_08BIT, &val))
      oc0tb1b_write_reg(client, OC0TB1B_REG_FSIN_OUT_SEL,
                        OC0TB1B_REG_VALUE_08BIT,
                        val & ~OC0TB1B_STROBE_OUT_SEL_REG);
  }
  /* Debug: print FSIN_CTRL and FSIN_OUT_SEL values */
  {
    u32 dbg_val;
    if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_CTRL,
                          OC0TB1B_REG_VALUE_08BIT, &dbg_val))
      dev_info(dev, "FSIN_CTRL (0x3006) = 0x%02x\n", dbg_val);
    else
      dev_warn(dev, "Failed to read FSIN_CTRL register\n");

    if (!oc0tb1b_read_reg(client, OC0TB1B_REG_FSIN_OUT_SEL,
                          OC0TB1B_REG_VALUE_08BIT, &dbg_val))
      dev_info(dev, "FSIN_OUT_SEL (0x3027) = 0x%02x\n", dbg_val);
    else
      dev_warn(dev, "Failed to read FSIN_OUT_SEL register\n");
  }

#ifdef CONFIG_VIDEO_V4L2_SUBDEV_API
  sd->internal_ops = NULL;
  sd->flags |= V4L2_SUBDEV_FL_HAS_DEVNODE;
#endif
#if defined(CONFIG_MEDIA_CONTROLLER)
  oc0tb1b->pad.flags = MEDIA_PAD_FL_SOURCE;
  sd->entity.function = MEDIA_ENT_F_CAM_SENSOR;
  ret = media_entity_pads_init(&sd->entity, 1, &oc0tb1b->pad);
  if (ret < 0)
    goto err_power_off;
#endif

  memset(facing, 0, sizeof(facing));
  if (strcmp(oc0tb1b->module_facing, "back") == 0)
    facing[0] = 'b';
  else
    facing[0] = 'f';

  snprintf(sd->name, sizeof(sd->name), "m%02d_%s_%s %s", oc0tb1b->module_index,
           facing, OC0TB1B_NAME, dev_name(dev));

  ret = v4l2_async_register_subdev_sensor(sd);
  if (ret) {
    dev_err(dev, "v4l2 async register subdev failed\n");
    goto err_clean_entity;
  }

  pm_runtime_set_active(dev);
  pm_runtime_enable(dev);
  pm_runtime_idle(dev);

  return 0;

err_clean_entity:
#if defined(CONFIG_MEDIA_CONTROLLER)
  media_entity_cleanup(&sd->entity);
#endif
err_power_off:
  __oc0tb1b_power_off(oc0tb1b);
err_free_handler:
  v4l2_ctrl_handler_free(&oc0tb1b->ctrl_handler);
err_destroy_mutex:
  mutex_destroy(&oc0tb1b->mutex);
  return ret;
}

static void oc0tb1b_remove(struct i2c_client *client) {
  struct v4l2_subdev *sd = i2c_get_clientdata(client);
  struct oc0tb1b *oc0tb1b = to_oc0tb1b(sd);

  v4l2_async_unregister_subdev(sd);
#if defined(CONFIG_MEDIA_CONTROLLER)
  media_entity_cleanup(&sd->entity);
#endif
  v4l2_ctrl_handler_free(&oc0tb1b->ctrl_handler);
  mutex_destroy(&oc0tb1b->mutex);

  pm_runtime_disable(&client->dev);
  if (!pm_runtime_status_suspended(&client->dev))
    __oc0tb1b_power_off(oc0tb1b);
  pm_runtime_set_suspended(&client->dev);
}

static const struct i2c_device_id oc0tb1b_match_id[] = {
    {"oc0tb1b", 0},
    {},
};

static const struct of_device_id oc0tb1b_of_match[] = {
    {.compatible = "ovti,oc0tb1b"},
    {},
};
MODULE_DEVICE_TABLE(of, oc0tb1b_of_match);

static struct i2c_driver oc0tb1b_i2c_driver = {
    .driver =
        {
            .name = OC0TB1B_NAME,
            .pm = &oc0tb1b_pm_ops,
            .of_match_table = of_match_ptr(oc0tb1b_of_match),
        },
    .probe = oc0tb1b_probe,
    .remove = oc0tb1b_remove,
    .id_table = oc0tb1b_match_id,
};

module_i2c_driver(oc0tb1b_i2c_driver);

MODULE_DESCRIPTION("OC0TB1B MIPI Camera Sensor Driver");
MODULE_LICENSE("GPL v2");
