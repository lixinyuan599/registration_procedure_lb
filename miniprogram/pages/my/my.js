Page({
  data: {
    nickname: '',
    avatarUrl: '',
    role: 'patient',
  },

  onLoad() {},

  onShow() {
    const app = getApp();
    this.setData({
      nickname: (app.globalData.userInfo && app.globalData.userInfo.nickname) || '',
      avatarUrl: (app.globalData.userInfo && app.globalData.userInfo.avatar_url) || '',
      role: app.globalData.role || 'patient',
    });
  },

  /** 我的预约 */
  goMyAppointments() {
    wx.switchTab({ url: '/pages/my-appointments/my-appointments' });
  },

  /** 排班设置 (医生) */
  goScheduleEdit() {
    wx.navigateTo({ url: '/pages/doctor-schedule-edit/doctor-schedule-edit' });
  },

  /** 个人信息 (预留) */
  goPersonalInfo() {
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },

  /** 关于系统 (预留) */
  goAbout() {
    wx.showToast({ title: '门诊挂号系统 v1.0.0', icon: 'none' });
  },
});
