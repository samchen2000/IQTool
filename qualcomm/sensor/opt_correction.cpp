#include <iostream>
 #include "RKOTPDLL.h"
 #include <stdlib.h>
 int main()
 {
    int ret = 0;
    // ret =lsc_awbtest();
    uint16_t gainmap[30*30 * 2];
    uint16_t dccmap[20 * 20 * 2];
    uint16_t code = 0;
    int gainmap_width = 0;
    int gainmap_height = 0;
    int dccmap_width = 0;
    int dccmap_height = 0;
    uint8_t dcc_Sign = 0;
    int curpos = 864;
    sensor_cfg sensor_param;
    if (pdaf_initial("D:\\testdll\\testdll\\sensor_ov50c.ini", &sensor_param))
    {
        if (gainmaptest(&sensor_param, gainmap,&gainmap_width,&gainmap_height))
        {
            if (dccmaptest(&sensor_param, gainmap, dccmap, curpos, &code, 
&dccmap_width, &dccmap_height, &dcc_Sign))
            {
                ret = dcc_calc_sharpness(&sensor_param);
            }
        }
    }
 }
 bool lsc_awbtest()
 {
    int height = 1944;
    int width = 2592;
    int bits =10;#10bit
    int bayer =0;#BGGR
    int roiw =5;#1/5 width
    int roih =5;#1/5 height
    int blc[4]={16,16,16,16};
    uint16_t lsctable[17*17*4];
    uint16_t awb[3];
    uint16_t Rave =0;
    uint16_t Grave =0;  
    uint16_t Gbave =0;
    uint16_t Bave =0;
    int Ydiffer_down =0;#%
    int Ydiffer_up =5;#%
    int ColorShading_down =0;#%
    int ColorShading_up =5;#%
    float Ydiffer = 0;
    float RGconer[25];
    float BGconer[25];
    bool ret =0;
    
    uint16_t *Rawdata = NULL;
    Rawdata = (uint16_t*)malloc(width * height * 2);
    memset(Rawdata, 0, sizeof(uint16_t)* width * height);
    
    FILE *fp = NULL;
    fp = fopen("input.raw", "rb");
    if (fp == NULL)
    {
        return false;
    }
    fread(Rawdata, 1, height * width * 2, fp);
    fclose(fp);
    
    ret =lsc_otp_Calibrate(Rawdata, width, height, bits, bayer, blc[0], 
blc[1],blc[2], blc[3], lsctable);
    ret = awb_otp_Calibrate(Rawdata, width, height,roiw,roih, bits, bayer, 
blc[0], blc[1],blc[2], blc[3],&Rave,&Grave,&Gbave,&Bave, &awb[0], &awb[1], 
&awb[2]);
    ret = lsc_otp_verify(Rawdata, width, height, bits, bayer, blc[0], blc[1], 
blc[2], blc[3], lsctable, Ydiffer_down, Ydiffer_up, ColorShading_down, 
ColorShading_up, &Ydiffer, RGconer, BGconer);
    if(!ret)
    {
        return false;   #标定后的数据不满足管控标准，验证失败
    }
    if(Rawdata!=NULL)
    {
        free (Rawdata);
        Rawdata =NULL;  
    }
    return ret;
 }
 int gainmaptest(sensor_cfg* psensor_cfg, uint16_t *gainmap_lut,int * 
gainmap_width, int *gainmap_height)
 {
    int ret = 0;
    int height = psensor_cfg->height;
    int width = psensor_cfg->width;
    uint16_t maxval = (1 << psensor_cfg->bits) - 1;
    int gainmapfilenum = 3;
    int over_exp_cnt = 0;
    uint16_t *ave_pixelbuf = NULL;
    ave_pixelbuf = (uint16_t*)malloc(width * height * 2);
    memset(ave_pixelbuf, 0, sizeof(uint16_t)* width * height);
    uint16_t *sum_pixelbuf = NULL;
    sum_pixelbuf = (uint16_t*)malloc(width * height * 2);
    memset(sum_pixelbuf, 0, sizeof(uint16_t)* width * height);
    uint16_t *pixelbuf = NULL;
    pixelbuf = (uint16_t*)malloc(width * height * 2);
    memset(pixelbuf, 0, sizeof(uint16_t)* width * height);
    FILE *fp = NULL;
    char prename[20] = "gainRAW";
    char endname[5] = ".raw";
    for (int i = 0; i < gainmapfilenum; i++)
    {
        char temp[20];
        char id[5];
        int idint = i + 1;
        strcpy(temp, prename);
        _itoa_s(idint, id, 10);
        strcat(temp, id);
        strcat(temp, endname);
        fp = fopen(temp, "rb");
        if (fp == NULL)
        {
            return false;
        }
        fread(pixelbuf, 1, height * width * 2, fp);
        fclose(fp);
        for (int j = 0; j < height; j++)
        {
            for (int i = 0; i < width; i++)
            {
                uint32_t tempbuf = *(pixelbuf + j*width + i);
                *(sum_pixelbuf + j*width + i) = tempbuf + *(sum_pixelbuf + 
j*width + i);
                if (tempbuf >= maxval)
                    over_exp_cnt++;
            }
        }
    }
    for (int j = 0; j < height; j++)
    {
        for (int i = 0; i < width; i++)
        {
            *(ave_pixelbuf + j*width + i) = *(sum_pixelbuf + j*width + i) / 
gainmapfilenum;
        }
    }
    if (over_exp_cnt > psensor_cfg->defect_pixel_num * gainmapfilenum) //allow 5 
defect pixels per image
    {
        printf("gainmap image OVER exposure!!!");
        if (ave_pixelbuf != NULL)
        {
            free(ave_pixelbuf);
            ave_pixelbuf = NULL;
        }
        if (pixelbuf != NULL)
        {
            free(pixelbuf);
            pixelbuf = NULL;
        }
        if (sum_pixelbuf != NULL)
        {
            free(sum_pixelbuf);
            sum_pixelbuf = NULL;
        }
        return -1;
    }
    ret = pdaf_gainmap_calibration(ave_pixelbuf, psensor_cfg, gainmap_lut, 
gainmap_width,gainmap_height);
    ret = pdaf_gainmap_vertification(ave_pixelbuf, psensor_cfg, gainmap_lut);
    if(ret == -1)
        printf("gainmap image OVER exposure!!!");
    if (ave_pixelbuf!=NULL)
    {
        free(ave_pixelbuf);
        ave_pixelbuf = NULL;
    }
    if (pixelbuf != NULL)
    {
        free(pixelbuf);
        pixelbuf = NULL;
    }
    if (sum_pixelbuf != NULL)
    {
        free(sum_pixelbuf);
        sum_pixelbuf = NULL;
    }
    return ret;
 }
 bool dccmaptest(sensor_cfg* psensor_cfg, uint16_t *gainmap_lut, uint16_t 
*dccmap_lut, int curpos , uint16_t *code, int *dccmap_width, int *dccmap_height, 
uint8_t *dcc_Sign)
 {
    int ret = 0;
    int lens_begin = 0;
    int lens_end = 64;
    int lens_interval = 8;
    int height = psensor_cfg->height;
    int width = psensor_cfg->width;
    int lensnum = (lens_end - lens_begin) / lens_interval + 1;
    uint16_t *ave_pixelbuf = NULL;
    ave_pixelbuf = (uint16_t*)malloc(width * height * 2);
    memset(ave_pixelbuf, 0, sizeof(uint16_t)* width * height);
    uint16_t *Rawdata = NULL;
    Rawdata = (uint16_t*)malloc(width * height * 2 * lensnum);
    memset(Rawdata, 0, sizeof(uint16_t)* width * height* lensnum);
    uint16_t *pixelbuf= NULL;
    pixelbuf = (uint16_t*)malloc(width * height * 2);
    memset(pixelbuf, 0, sizeof(uint16_t)* width * height);
    FILE *fp = NULL;
    char prename[20] = "dccRAW";
    char endname[5] = ".raw";
    for (int a = 0;a <lensnum;a++)
    {
        char temp[20];
        char id[5] ;
        int id1 = a + 1;
        strcpy(temp,prename);
        _itoa_s(id1, id, 10);
        strcat(temp, id);
        
        for (int b = 0; b < 3;b++)
        {
            char name[20];
            strcpy(name, temp);
            int id2 = b + 1;
            _itoa_s(id2, id, 10);
            strcat(name, id);
            strcat(name, endname);
            fp = fopen(name, "rb");
            if (fp == NULL)
            {
                return false;
            }
            fread(pixelbuf, 1, height * width * 2, fp);
            fclose(fp);
            for (int j = 0; j < height; j++)
            {
                for (int i = 0; i < width; i++)
                {
                    uint16_t tempbuf = *(ave_pixelbuf + j*width + i);
                    *(ave_pixelbuf + j*width + i) = tempbuf + *(pixelbuf + 
j*width + i) / 3;
                }
            }
        }
        memcpy(Rawdata + a*height * width, ave_pixelbuf, sizeof(uint16_t)*height 
* width);
        memset(ave_pixelbuf, 0, sizeof(uint16_t)* width * height);
    }
    ret = pdaf_dccmap_calibration(Rawdata, psensor_cfg, gainmap_lut, dccmap_lut, 
dccmap_width, dccmap_height, dcc_Sign);
    memset(pixelbuf, 0, sizeof(uint16_t)* width * height);
    memset(ave_pixelbuf, 0, sizeof(uint16_t)* width * height);
    char prename1[20] = "image";
    for (int i = 0; i < 3; i++)
    {
        char temp[20];
        char id[5];
        int idint = i + 1;
        strcpy(temp, prename1);
        _itoa_s(idint, id, 10);
        strcat(temp, id);
        strcat(temp, endname);
        fp = fopen(temp, "rb");
        if (fp == NULL)
        {
            return false;
        }
        fread(pixelbuf, 1, height * width * 2, fp);
        fclose(fp);
        for (int j = 0; j < height; j++)
        {
            for (int i = 0; i < width; i++)
            {
                uint16_t tempbuf = *(ave_pixelbuf + j*width + i);
                *(ave_pixelbuf + j*width + i) = tempbuf + *(pixelbuf + j*width + 
i) / 3;
            }
        }
    }
    *code = pdaf_dccmap_vertification(ave_pixelbuf, psensor_cfg, curpos, 
gainmap_lut, dccmap_lut, *dcc_Sign);
    if (ave_pixelbuf != NULL)
    {
        free(ave_pixelbuf);
        ave_pixelbuf = NULL;
    }
    if (pixelbuf != NULL)
    {
        free(pixelbuf);
        pixelbuf = NULL;
    }
    if (Rawdata != NULL)
    {
        free(Rawdata);
        Rawdata = NULL;
    }
    return ret;
 }
 bool dcc_calc_sharpness(sensor_cfg* psensor_cfg)
 {
    int height = psensor_cfg->height;
    int width = psensor_cfg->width;
    int imgnum = 5;
    uint16_t *Rawdata = NULL;
    Rawdata = (uint16_t*)malloc(width * height * 2 * imgnum);
    memset(Rawdata, 0, sizeof(uint16_t)* width * height* imgnum);
    uint16_t *pixelbuf = NULL;
    pixelbuf = (uint16_t*)malloc(width * height * 2);
    memset(pixelbuf, 0, sizeof(uint16_t)* width * height);
    FILE *fp = NULL;
    char prename[20] = "calimage";
    char endname[5] = ".raw";
    for (int i = 0; i < imgnum; i++)
    {
        char temp[20];
        char id[5];
        int idint = i + 1;
        strcpy(temp, prename);
        _itoa_s(idint, id, 10);
        strcat(temp, id);
        strcat(temp, endname);
fp = fopen(temp, "rb");
 if (fp == NULL)
 {
 return false;
 }
 fread(pixelbuf, 1, height * width * 2, fp);
 fclose(fp);
 memcpy(Rawdata + i*height * width, pixelbuf, sizeof(uint16_t)*height * 
width);
 }
 bool ret=pdaf_calc_sharpness(Rawdata, imgnum, psensor_cfg);
 if (pixelbuf != NULL)
 {
 free(pixelbuf);
 pixelbuf = NULL;
 }
 if (Rawdata != NULL)
 {
 free(Rawdata);
 Rawdata = NULL;
 }
 return ret;
 }