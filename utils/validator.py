def validate_phone(phone):
    """验证手机号（11位数字）"""
    return len(phone) == 11 and phone.isdigit()

def validate_decimal(value):
    """验证数字（整数/小数）"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def validate_positive_int(value):
    """验证正整数"""
    try:
        # 检查是否为空字符串
        if value is None or str(value).strip() == '':
            return False
        return int(value) > 0
    except (ValueError, TypeError):
        return False

def validate_required(fields):
    """验证必填字段"""
    for field_name, field_value in fields.items():
        if not field_value or str(field_value).strip() == '':
            return False, f'{field_name}不能为空'
    return True, ''