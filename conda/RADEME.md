## conda 常用指令
### 建立虛擬環境
Conda 指令主要用於管理 Python 環境與套件，核心功能包括：建立新環境 (conda create)、激活環境 (conda activate)、退出環境 (conda deactivate)、安裝套件 (conda install)、列出套件 (conda list)、移除套件或環境 (conda remove)，以及管理環境列表 (conda env list)，讓你輕鬆隔離不同專案的Python 版本與依賴。  

### 環境管理
列出所有環境: 
```
conda env list
```  
建立新環境: 
```
conda create --name myenv python=3.10 (建立名為myenv 且包含Python 3.10 的環境)
```
激活環境: 
```
conda activate myenv (進入myenv 環境)
```
退出環境: 
```
conda deactivate (回到base 環境)
```
移除環境: 
```
conda env remove --name myenv
```
複製環境: 
```
conda create --name new_env --clone old_env 
```
### 套件管理
列出套件: 
```
conda list (查看當前環境的套件)
```
安裝套件: 
```
conda install package_name
```
安裝指定版本套件: 
```
conda install package_name=1.2.3
```
從檔案安裝: 
```
conda install --file requirements.txt
```
更新套件: 
```
conda update package_name
```
移除套件: 
```
conda remove package_name 
```
### Conda 自身管理
查看版本: 
```
conda --version or conda -V
```
更新Conda: 
```
conda update conda
```
查看幫助: 
```
conda --help or conda install --help 
```
### 進階應用
匯出環境: 
```
conda env export > environment.yml (用於分享或重現環境)
```
從檔案建立環境: 
```
conda env create -f environment.yml 
```