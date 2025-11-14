from importlib import util
import traceback

spec = util.spec_from_file_location("LDC_test", r"d:\IQ app\python\IQTool\qualcomm\LDC\LDC_test.py")
mod = util.module_from_spec(spec)
spec.loader.exec_module(mod)

# 選一張工作區內的圖，若不是棋盤格會產生例外
img = r"d:\IQ app\python\IQTool\IQ Tool\image test\IMG_1974.jpg"
# 常見棋盤內角點設定 (cols, rows)
pattern = (9, 6)
# 每格大小 (mm)
square_mm = 25.0

print(f"Running calculate_distortion on: {img}\npattern={pattern}, square_size_mm={square_mm}")
try:
    tv_val, data = mod.calculate_distortion(img, pattern, square_mm)
    print("TV Distortion (%):", tv_val)
    print("Returned keys:", list(data.keys()))
    print("r_max:", data.get('r_max'))
    print("max_idx:", data.get('max_idx'))
    print("num points:", len(data.get('ideal_points', [])))
except Exception as e:
    print("Exception raised while running calculate_distortion:\n")
    traceback.print_exc()
