from datetime import datetime, date


def parse_datetime(date_str, default_format=None):
    """
    解析日期时间字符串
    
    Args:
        date_str: 日期时间字符串
        default_format: 默认格式，如果为None则尝试多种常见格式
        
    Returns:
        datetime: 解析后的datetime对象，如果解析失败返回None
    """
    if default_format:
        try:
            return datetime.strptime(date_str, default_format)
        except (ValueError, TypeError):
            return None
    
    # 尝试多种常见格式
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    
    return None


def calculate_time_remaining(deadline_str):
    """
    计算剩余时间（用于任务排序）
    
    Args:
        deadline_str: 截止日期字符串
        
    Returns:
        tuple: (has_deadline, is_overdue, remaining_seconds)
    """
    if deadline_str == "无截止日期":
        return (False, False, float('inf'))
    
    deadline_datetime = parse_datetime(deadline_str)
    if not deadline_datetime:
        return (False, False, float('inf'))
    
    now = datetime.now()
    time_diff = deadline_datetime - now
    remaining_seconds = time_diff.total_seconds()
    
    return (True, remaining_seconds <= 0, remaining_seconds)


def format_time_remaining(deadline_str):
    """
    格式化剩余时间显示文本
    
    Args:
        deadline_str: 截止日期字符串
        
    Returns:
        str: 格式化的剩余时间文本
    """
    if deadline_str == "无截止日期":
        return "无截止日期"
    
    try:
        # 尝试解析包含时间的格式
        try:
            deadline_datetime = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
        except ValueError:
            # 回退到旧格式（仅日期）
            deadline_datetime = datetime.strptime(deadline_str, "%Y-%m-%d")
        
        now = datetime.now()
        time_diff = deadline_datetime - now
        total_seconds = time_diff.total_seconds()
        
        is_overdue = total_seconds <= 0
        if is_overdue:
            total_seconds = abs(total_seconds)
        
        # 计算时间分量
        days = int(total_seconds // (24 * 3600))
        hours = int((total_seconds % (24 * 3600)) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0 or not parts:  # 至少显示分钟
            parts.append(f"{minutes}分钟")
        # 当小时和天都为0时，显示秒数
        if not days and not hours:
            parts.append(f"{seconds}秒")
        
        prefix = "已超时: " if is_overdue else "剩余: "
        return f"{prefix}{' '.join(parts)}"
    except Exception:
        return "时间格式错误"


def get_target_urgency(deadline_str):
    """
    根据截止日期计算目标紧急度
    
    Args:
        deadline_str: 截止日期字符串
        
    Returns:
        int: 目标紧急度（1最紧急，10最不紧急）
    """
    if deadline_str == "无截止日期":
        return 10  # 无截止日期默认最低紧急度
    
    deadline_datetime = parse_datetime(deadline_str)
    if not deadline_datetime:
        return 10  # 解析失败默认最低紧急度
    
    now = datetime.now()
    time_remaining = deadline_datetime - now
    hours_remaining = time_remaining.total_seconds() / 3600
    
    # 根据剩余时间计算紧急度
    if hours_remaining <= 0:
        return 1  # 超时未处理
    elif hours_remaining <= 2:
        return 2  # 极度紧急：0-2小时内完成
    elif hours_remaining <= 8:
        return 3  # 极高紧急：2-8小时内完成
    elif hours_remaining <= 24:
        return 4  # 高紧急：8-24小时内完成
    elif hours_remaining <= 48:
        return 5  # 较紧急：2天内完成
    elif hours_remaining <= 120:
        return 6  # 中紧急：3-5天内完成
    elif hours_remaining <= 168:
        return 7  # 常规紧急：1周内完成
    elif hours_remaining <= 336:
        return 8  # 低紧急：2-3周内完成
    elif hours_remaining <= 1008:
        return 9  # 极低紧急：1个月内完成
    else:
        return 10  # 长期规划：1个月以上
