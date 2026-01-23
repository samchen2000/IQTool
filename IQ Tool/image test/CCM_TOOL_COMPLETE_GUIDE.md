# ccm_test_3.py - 完整功能说明

## 概述

ccm_test_3.py 是一个互动式 CCM（色彩校正矩阵）调整工具，结合了标准 24 色标准色卡和自定义图片模式。

## 核心功能

### 1. 标准模式（默认）
- 加载标准 24 色 Macbeth ColorChecker
- 支持 9 个 CCM 参数的滑块调整
- 支持增加/减少按键（±0.05）
- 支持直接输入框编辑

### 2. 手动图片模式（新增）
- 打开自定义图片（JPEG/PNG/BMP）
- 自动检测 24 色块位置
- 手动调整方框位置和大小
- 实时 Lab 值更新

### 3. 菜单栏（新增）
```
File
├── Open Image (JPEG/PNG/BMP)  # 打开图片
└── Exit                        # 退出程序
```

## 使用流程

### 标准模式使用
1. 运行程序
2. 默认加载 24 色标准色卡
3. 使用滑块、按键或输入框调整 CCM 参数
4. 在左侧查看原始色卡，右侧查看调整后的色卡
5. 在 Lab 分析窗口查看实时数据

### 手动图片模式使用
1. 运行程序
2. 点击菜单 **File → Open Image**
3. 选择图片文件（JPEG/PNG/BMP）
4. 系统自动：
   - 缩放图片以适应显示区域
   - 检测 24 个色块位置
   - 生成可调整的方框
5. 调整方框位置和大小：
   - **点击方框**：选中（边框变红）
   - **拖拽**：移动方框
   - **Shift + 拖拽**：调整大小
6. 实时查看 Lab 值变化

## 技术实现

### 自动色块检测
```
算法：K-means 聚类
步骤：
1. 将图像转换为像素列表
2. 使用 cv2.kmeans 进行 24 类聚类
3. 为每个聚类计算边界框
4. 按 (y, x) 坐标排序
```

### 颜色提取
```
流程：
1. 获取方框内所有像素
2. 计算平均 RGB 值
3. 应用 CCM 矩阵变换
4. 转换为 Lab 色彩空间
5. 更新 Lab 显示窗口
```

### 鼠标交互
```
事件处理：
- button_press_event      → 记录起始点
- motion_notify_event     → 移动或调整大小
- button_release_event    → 结束操作
- pick_event              → 选择方框或输入框

操作模式：
- 默认拖拽 → 移动方框
- Shift + 拖拽 → 调整方框大小
```

## 全局数据结构

```python
global_data = {
    # 标准模式数据
    'lab_values': [],                    # Lab 值列表
    'color_names': [],                   # 颜色名称
    'text_widget': None,                 # Lab 显示窗口
    'colors_rgb_original': [],           # 原始 RGB 颜色
    'current_ccm': np.eye(3),            # 当前 CCM 矩阵
    
    # Matplotlib 对象
    'fig': None,
    'ax': None,
    'img_display': None,                 # 图像显示对象
    'ax_adjusted': None,                 # 右侧 axis
    
    # 手动模式数据
    'user_image': None,                  # 用户打开的图片
    'user_image_display': None,          # 用户图片显示对象
    'color_boxes': [],                   # 方框对象列表
    'is_manual_mode': False,             # 是否手动模式
    'box_positions': [],                 # 方框位置信息
    'selected_box_idx': None,            # 当前选中方框
}
```

## 关键函数

### 图片处理
| 函数 | 说明 |
|------|------|
| `open_image_file()` | 打开文件对话框并加载图片 |
| `detect_color_blocks_kmeans()` | 自动检测 24 色块位置 |
| `load_user_image_to_plot()` | 将用户图片加载到 Matplotlib |
| `create_initial_boxes()` | 创建初始 24 个方框 |

### 数据更新
| 函数 | 说明 |
|------|------|
| `update()` | CCM 滑块更新回调 |
| `update_manual_mode_display()` | 手动模式 Lab 值更新 |
| `update_text_display()` | 更新 Lab 显示窗口 |

### 事件处理
| 函数 | 事件类型 | 说明 |
|------|---------|------|
| `on_open_image()` | 菜单点击 | 打开图片 |
| `on_box_pick_event()` | pick_event | 选择方框 |
| `on_mouse_press()` | button_press_event | 鼠标按下 |
| `on_mouse_motion()` | motion_notify_event | 鼠标移动/调整 |
| `on_mouse_release()` | button_release_event | 鼠标释放 |

## 文件结构

```
d:\IQ app\python\IQTool\IQ Tool\image test\
├── ccm_test_3.py                    # 主程序
├── MANUAL_IMAGE_MODE.md             # 手动模式使用指南
├── CHANGES.md                       # 版本更新说明
└── USAGE_GUIDE.md                   # 通用使用指南
```

## 特色功能

### ✅ 已实现
- [x] 菜单栏（File 菜单）
- [x] 打开图片对话框（支持 JPEG/PNG/BMP）
- [x] 自动色块检测（K-means）
- [x] 可拖拽方框
- [x] 方框大小调整（Shift + 拖拽）
- [x] 实时 Lab 值更新
- [x] 菜单栏集成
- [x] 图片尺寸自动调整
- [x] 方框颜色反馈（选中变红）

### 🚀 可扩展方向
- 方框网格对齐功能
- 撤销/重做功能
- 保存/加载方框配置
- 批量图片处理
- 色块验证报告
- 高级色彩分析

## 注意事项

### 性能
- 自动检测大图片可能需要数秒
- 建议图片分辨率 ≤ 2000×2000
- 每次调整时会实时更新（可能较慢）

### 兼容性
- 支持 Windows、macOS、Linux
- 需要 OpenCV、NumPy、Matplotlib、scikit-image
- Python 3.7+

### 边界处理
- 方框会自动限制在图片范围内
- 超出范围的像素会被自动裁剪
- 颜色计算会跳过无效区域

## 快速参考

### 标准模式快捷键
| 操作 | 说明 |
|------|------|
| 拖拽滑块 | 调整 CCM 参数 |
| 点击 ± 按键 | 增加/减少 0.05 |
| 点击输入框 | 直接编辑数值 |
| Enter | 确认输入 |
| Escape | 取消编辑 |

### 手动模式快捷键
| 操作 | 说明 |
|------|------|
| File → Open | 打开图片 |
| 点击方框 | 选中方框 |
| 拖拽 | 移动方框 |
| Shift + 拖拽 | 调整大小 |
| File → Exit | 退出 |

## 常见问题解答

### Q: 如何切换回标准色卡？
A: 重新运行程序或在代码中注释掉 `open_image_file()` 相关代码。

### Q: 自动检测精度不够高？
A: 可手动调整方框位置和大小。对于复杂背景的图片，检测可能不准确。

### Q: 方框数量为什么是 24 个？
A: 对应标准 Macbeth ColorChecker 的 24 色色块规格。

### Q: 如何提高检测速度？
A: 使用较小分辨率的图片（< 1000×1000 像素）。

### Q: 能否保存调整结果？
A: 目前可通过截图保存。未来版本将支持数据导出。

## 联系与反馈

如有问题或建议，请在项目中提交 Issue 或 Pull Request。

---

**最后更新**: 2026-01-23
**版本**: 3.0 (手动图片模式版)
