/**
 * 预约确认页
 * 展示预约信息摘要，用户确认后提交预约
 */
const api = require('../../services/api');

Page({
  data: {
    scheduleId: 0,
    doctorId: 0,
    clinicId: 0,
    doctorName: '',
    expertise: '',
    date: '',
    timeSlot: '',
    remaining: 0,
    clinicName: '',
    notes: '',
    submitting: false,
  },

  onLoad(options) {
    const app = getApp();
    const clinic = app.globalData.selectedClinic;

    this.setData({
      scheduleId: parseInt(options.scheduleId),
      doctorId: parseInt(options.doctorId),
      clinicId: parseInt(options.clinicId),
      doctorName: decodeURIComponent(options.doctorName || ''),
      expertise: decodeURIComponent(options.expertise || ''),
      date: options.date || '',
      timeSlot: decodeURIComponent(options.timeSlot || ''),
      remaining: parseInt(options.remaining || 0),
      clinicName: clinic ? clinic.name : '',
    });
  },

  /**
   * 备注输入
   */
  onNotesInput(e) {
    this.setData({ notes: e.detail.value });
  },

  /**
   * 提交预约
   */
  async onSubmit() {
    if (this.data.submitting) return;

    this.setData({ submitting: true });
    try {
      const result = await api.createAppointment({
        doctor_id: this.data.doctorId,
        clinic_id: this.data.clinicId,
        schedule_id: this.data.scheduleId,
        notes: this.data.notes || null,
      });

      wx.showToast({ title: '预约成功', icon: 'success', duration: 1500 });

      // 延迟跳转到我的预约页
      setTimeout(() => {
        wx.switchTab({ url: '/pages/my-appointments/my-appointments' });
      }, 1500);
    } catch (err) {
      console.error('预约失败:', err);
      this.setData({ submitting: false });
    }
  },
});
