/**
 * 医生挂号列表页
 * 医生查看自己的挂号患者列表，按排队号排序
 */
const api = require('../../services/api');
const util = require('../../utils/util');

Page({
  data: {
    selectedDate: '',
    dateOptions: [],
    appointments: [],
    loading: true,
    totalCount: 0,
  },

  onLoad() {
    this._initDates();
    this.loadQueue();
  },

  onShow() {
    this.loadQueue();
  },

  onPullDownRefresh() {
    this.loadQueue().then(() => wx.stopPullDownRefresh());
  },

  _initDates() {
    const today = new Date();
    const dates = [];
    for (let i = -1; i <= 6; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() + i);
      const dateStr = util.formatDate(d);
      const weekDay = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()];
      let label = `${dateStr} ${weekDay}`;
      if (i === 0) label = `今天 (${dateStr})`;
      else if (i === 1) label = `明天 (${dateStr})`;
      else if (i === -1) label = `昨天 (${dateStr})`;
      dates.push({ value: dateStr, label });
    }
    this.setData({
      dateOptions: dates,
      selectedDate: dates[1].value,
    });
  },

  onDateChange(e) {
    const idx = e.detail.value;
    this.setData({ selectedDate: this.data.dateOptions[idx].value });
    this.loadQueue();
  },

  async loadQueue() {
    this.setData({ loading: true });
    try {
      const app = getApp();
      await app.ensureLogin();
      const list = await api.getDoctorQueue(this.data.selectedDate);
      const processed = (list || []).map((item, idx) => ({
        ...item,
        displayQueue: item.queue_number || (idx + 1),
        dateLabel: util.friendlyDate(item.appointment_date),
        statusText: util.getStatusInfo(item.status).text,
        statusClass: util.getStatusInfo(item.status).tagClass,
      }));
      this.setData({
        appointments: processed,
        totalCount: processed.length,
        loading: false,
      });
    } catch (err) {
      console.error('加载挂号列表失败:', err);
      this.setData({ loading: false });
      if (err.code === 403) {
        wx.showToast({ title: '仅医生可查看', icon: 'none' });
      }
    }
  },
});
