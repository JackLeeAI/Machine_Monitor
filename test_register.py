import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.auth_service import AuthService

try:
    # 测试注册功能
    print('开始测试注册功能...')
    user = AuthService.register(
        username='test_user',
        password='123456',
        email='test@example.com',
        phone='13800138000',
        position='技术员'
    )
    print(f'注册成功！用户ID: {user.user_id}, 职工ID: {user.person_id}')
    print('测试通过！')
except Exception as e:
    print(f'注册失败: {e}')
    print('测试失败！')
    import traceback
    traceback.print_exc()
