#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenISP GUI - 環境驗證腳本
檢查所有必需的依賴和模塊
"""

import sys
from pathlib import Path

def check_environment():
    """檢查環境配置"""
    print("=" * 60)
    print("OpenISP GUI - 環境驗證")
    print("=" * 60)
    
    # 檢查Python版本
    print(f"\n✓ Python 版本: {sys.version}")
    if sys.version_info < (3, 7):
        print("✗ 錯誤: 需要 Python 3.7 或更新版本")
        return False
    
    # 檢查必需模塊
    required_modules = {
        'numpy': 'NumPy',
        'PIL': 'Pillow (圖像處理)',
        'tkinter': 'Tkinter (GUI框架)',
    }
    
    print("\n必需模塊檢查:")
    for module, name in required_modules.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {module} - 未安裝")
            return False
    
    # 檢查可選模塊
    optional_modules = {
        'PyQt5': 'PyQt5 (可選 - 高級GUI)',
        'cv2': 'OpenCV (可選)',
        'matplotlib': 'Matplotlib (可選)',
    }
    
    print("\n可選模塊檢查:")
    for module, name in optional_modules.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ○ {module} - 未安裝 (不影響使用)")
    
    # 檢查ISP模塊
    print("\nISP模塊檢查:")
    model_dir = Path('./model')
    if not model_dir.exists():
        print("  ✗ 錯誤: model/ 文件夾不存在")
        return False
    
    required_models = [
        'dpc.py', 'blc.py', 'aaf.py', 'awb.py', 'cnf.py',
        'cfa.py', 'gac.py', 'ccm.py', 'csc.py', 'bnf.py',
        'eeh.py', 'fcs.py', 'bcc.py', 'hsc.py', 'nlm.py'
    ]
    
    all_found = True
    for model_file in required_models:
        if (model_dir / model_file).exists():
            print(f"  ✓ {model_file}")
        else:
            print(f"  ✗ {model_file} - 未找到")
            all_found = False
    
    if not all_found:
        return False
    
    # 檢查配置文件
    print("\n配置文件檢查:")
    config_dir = Path('./config')
    if not config_dir.exists():
        print("  ✗ 錯誤: config/ 文件夾不存在")
        return False
    
    if (config_dir / 'config.csv').exists():
        print("  ✓ config/config.csv")
    else:
        print("  ✗ config/config.csv - 未找到")
        return False
    
    # 檢查測試數據
    print("\n測試數據檢查:")
    raw_dir = Path('./raw')
    if not raw_dir.exists():
        print("  ✓ raw/ - 文件夾存在")
    elif (raw_dir / 'test.RAW').exists():
        print("  ✓ raw/test.RAW")
    else:
        print("  ○ raw/test.RAW - 未找到 (需要自己加載)")
    
    return True


def test_imports():
    """測試導入ISP模塊"""
    print("\n" + "=" * 60)
    print("ISP 模塊導入測試")
    print("=" * 60 + "\n")
    
    try:
        from model.dpc import DPC
        print("✓ DPC - 死像素矯正")
        
        from model.blc import BLC
        print("✓ BLC - 黑電平補償")
        
        from model.aaf import AAF
        print("✓ AAF - 防黑混淆濾波")
        
        from model.awb import WBGC
        print("✓ WBGC - 白平衡增益")
        
        from model.cnf import CNF
        print("✓ CNF - 色度噪聲濾波")
        
        from model.cfa import CFA
        print("✓ CFA - 去馬賽克")
        
        from model.gac import GC
        print("✓ GC - 伽馬校正")
        
        from model.ccm import CCM
        print("✓ CCM - 色彩校正")
        
        from model.csc import CSC
        print("✓ CSC - 色彩空間轉換")
        
        from model.bnf import BNF
        print("✓ BNF - 雙邊濾波")
        
        from model.eeh import EE
        print("✓ EE - 邊緣增強")
        
        from model.fcs import FCS
        print("✓ FCS - 假色抑制")
        
        from model.bcc import BCC
        print("✓ BCC - 亮度/對比度")
        
        from model.hsc import HSC
        print("✓ HSC - 色調/飽和度")
        
        from model.nlm import NLM
        print("✓ NLM - 非局部均值去噪")
        
        print("\n✓ 所有ISP模塊導入成功!")
        return True
        
    except ImportError as e:
        print(f"\n✗ 導入失敗: {e}")
        return False


def print_summary():
    """打印總結"""
    print("\n" + "=" * 60)
    print("🎉 環境驗證完成!")
    print("=" * 60)
    
    print("\n下一步:")
    print("1. 安裝依賴 (如需):")
    print("   pip install -r REQUIREMENTS.txt")
    print("\n2. 啟動 Tkinter 版本 (推薦):")
    print("   python isp_gui_tkinter.py")
    print("\n3. 或啟動 PyQt5 版本:")
    print("   python isp_gui_app.py")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    success = True
    
    if check_environment():
        if test_imports():
            print_summary()
        else:
            success = False
    else:
        success = False
    
    sys.exit(0 if success else 1)
