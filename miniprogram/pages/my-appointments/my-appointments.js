/**
 * 我的预约页
 * 展示用户的所有预约记录，支持取消预约
 */
const api = require('../../services/api');
const util = require('../../utils/util');

const app = getApp();

Page({
  data: {
    appointments: [],
    loading: true,
  },

  onShow() {
    // 每次进入页面都刷新数据 (从预约确认页跳转过来时)
    this.loadAppointments();
  },

  onPullDownRefresh() {
    this.loadAppointments().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 加载预约列表
   */
  async loadAppointments() {
    this.setData({ loading: true });
    try {
      const appointments = await api.getMyAppointments();
      // 为每个预约添加状态展示信息
      const list = appointments.map((apt) => {
        const statusInfo = util.getStatusInfo(apt.status);
        return {
          ...apt,
          statusText: statusInfo.text,
          statusClass: statusInfo.tagClass,
          dateLabel: util.friendlyDate(apt.appointment_date),
        };
      });
      this.setData({ appointments: list, loading: false });
    } catch (err) {
      console.error('加载预约失败:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * 取消预约
   */
  onCancelTap(e) {
    const appointment = e.currentTarget.dataset.appointment;

    wx.showModal({
      title: '取消预约',
      content: `确定要取消 ${appointment.doctor.name} 医生 ${appointment.appointment_date} ${appointment.time_slot} 的预约吗？`,
      confirmText: '确定取消',
      confirmColor: '#FF4D4F',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.cancelAppointment(appointment.id);
            wx.showToast({ title: '已取消预约', icon: 'success' });
            this.loadAppointments();
          } catch (err) {
            console.error('取消预约失败:', err);
          }
        }
      },
    });
  },
});
