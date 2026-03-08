#!/usr/bin/env python3
import os
import subprocess
import shutil
import json
import time

# 指定測試圖片（如果有的話，否則提示用戶）
TEST_IMAGE = "openclaw/test_card.jpg" # 或用戶提供的路徑

def run_test(mode):
    print(f"🚀 正在測試 OpenClaw 模式: {mode.upper()}...")
    debug_dir = f"debug/openclaw_test_{mode}_{int(time.time())}"
    cmd = [
        "python3", "scripts/openclaw_facade.py",
        TEST_IMAGE,
        "--mode", mode,
        "--debug", debug_dir
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {mode.upper()} 模式測試成功！")
            print(f"📁 輸出結果已儲存至: {debug_dir}")
            # 這裡就不印出具體的 JSON 以免刷屏
        else:
            print(f"❌ {mode.upper()} 模式測試失敗！")
            print(f"錯誤訊息: {result.stderr}")
    except Exception as e:
        print(f"💥 執行出錯: {e}")

if __name__ == "__main__":
    if not os.path.exists(TEST_IMAGE):
        print(f"⚠️ 找不到預設測試圖片: {TEST_IMAGE}。請手動運行測試指令：")
        print(f"python3 scripts/openclaw_facade.py <你的圖片路徑> --mode json")
    else:
        run_test("json")
        print("-" * 40)
        run_test("full")
