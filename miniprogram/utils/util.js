/**
 * 工具函数
 */

/**
 * 格式化日期为 YYYY-MM-DD
 */
function formatDate(date) {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 格式化时间 HH:MM:SS -> HH:MM
 */
function formatTime(timeStr) {
  if (!timeStr) return '';
  return timeStr.substring(0, 5);
}

/**
 * 获取星期几
 */
function getWeekDay(dateStr) {
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  const d = new Date(dateStr);
  return days[d.getDay()];
}

/**
 * 判断是否是今天
 */
function isToday(dateStr) {
  return formatDate(new Date()) === dateStr;
}

/**
 * 判断是否是明天
 */
function isTomorrow(dateStr) {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return formatDate(tomorrow) === dateStr;
}

/**
 * 获取友好的日期显示
 * 如: 今天、明天、02-18 周三
 */
function friendlyDate(dateStr) {
  if (isToday(dateStr)) return '今天';
  if (isTomorrow(dateStr)) return '明天';
  const weekDay = getWeekDay(dateStr);
  const parts = dateStr.split('-');
  return `${parts[1]}-${parts[2]} ${weekDay}`;
}

/**
 * 预约状态映射
 */
function getStatusInfo(status) {
  const map = {
    confirmed: { text: '已确认', tagClass: 'tag-green' },
    cancelled: { text: '已取消', tagClass: 'tag-gray' },
    completed: { text: '已完成', tagClass: 'tag-blue' },
  };
  return map[status] || { text: status, tagClass: 'tag-gray' };
}

module.exports = {
  formatDate,
  formatTime,
  getWeekDay,
  isToday,
  isTomorrow,
  friendlyDate,
  getStatusInfo,
};
