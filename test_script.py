import sys
import traceback

try:
    from message.dlt_ssq_script import generate_lottery_numbers
    result = generate_lottery_numbers(1)
    print(f"生成结果: {result}")
except Exception as e:
    print(f"错误: {e}")
    traceback.print_exc()