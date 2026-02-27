const api = require('../../services/api');
const app = getApp();

Page({
  data: {
    nickname: '',
    avatarUrl: '',
    role: 'patient',
    doctorId: null,
    doctorName: '',
    showBindModal: false,
    inviteCode: '',
    binding: false,
  },

  onLoad() {},

  onShow() {
    this._refreshProfile();
  },

  async _refreshProfile() {
    const role = app.globalData.role || 'patient';
    const doctorId = app.globalData.doctorId || null;

    this.setData({
      nickname: (app.globalData.userInfo && app.globalData.userInfo.nickname) || '',
      avatarUrl: (app.globalData.userInfo && app.globalData.userInfo.avatar_url) || '',
      role,
      doctorId,
    });

    try {
      await app.ensureLogin();
      const profile = await api.getMyProfile();
      if (profile) {
        app.globalData.role = profile.role || 'patient';
        app.globalData.doctorId = profile.doctor_id || null;
        wx.setStorageSync('role', app.globalData.role);
        wx.setStorageSync('doctorId', app.globalData.doctorId);

        this.setData({
          role: profile.role || 'patient',
          doctorId: profile.doctor_id || null,
          doctorName: profile.doctor_name || '',
          nickname: profile.nickname || '',
        });
      }
    } catch (e) {
      console.log('获取用户信息失败', e);
    }
  },

  /** 我的预约 */
  goMyAppointments() {
    wx.switchTab({ url: '/pages/my-appointments/my-appointments' });
  },

  /** 排班设置 (医生) */
  goScheduleEdit() {
    wx.navigateTo({ url: '/pages/doctor-schedule-edit/doctor-schedule-edit' });
  },

  /** 打开医生认证弹窗 */
  openBindModal() {
    this.setData({ showBindModal: true, inviteCode: '', binding: false });
  },

  /** 关闭弹窗 */
  closeBindModal() {
    this.setData({ showBindModal: false });
  },

  /** 输入邀请码 */
  onInviteCodeInput(e) {
    this.setData({ inviteCode: e.detail.value });
  },

  /** 提交邀请码绑定 */
  async onSubmitBind() {
    const code = this.data.inviteCode.trim();
    if (!code) {
      wx.showToast({ title: '请输入邀请码', icon: 'none' });
      return;
    }
    if (this.data.binding) return;
    this.setData({ binding: true });

    try {
      const result = await api.bindDoctor(code);
      app.globalData.role = result.role;
      app.globalData.doctorId = result.doctor_id;
      wx.setStorageSync('role', result.role);
      wx.setStorageSync('doctorId', result.doctor_id);

      this.setData({
        showBindModal: false,
        role: result.role,
        doctorId: result.doctor_id,
        doctorName: result.doctor_name || '',
      });

      wx.showToast({ title: '认证成功', icon: 'success' });
    } catch (e) {
      console.error('绑定失败:', e);
    } finally {
      this.setData({ binding: false });
    }
  },

  /** 解除医生绑定 */
  async onUnbindDoctor() {
    const res = await new Promise(resolve => {
      wx.showModal({
        title: '提示',
        content: '确定解除医生身份吗？解除后将无法管理排班。',
        success: resolve,
      });
    });
    if (!res.confirm) return;

    try {
      await api.unbindDoctor();
      app.globalData.role = 'patient';
      app.globalData.doctorId = null;
      wx.setStorageSync('role', 'patient');
      wx.setStorageSync('doctorId', null);

      this.setData({
        role: 'patient',
        doctorId: null,
        doctorName: '',
      });
      wx.showToast({ title: '已解除', icon: 'success' });
    } catch (e) {
      console.error('解绑失败:', e);
    }
  },

  /** 个人信息 (预留) */
  goPersonalInfo() {
    wx.showToast({ title: '功能开发中', icon: 'none' });
  },

  /** 关于系统 */
  goAbout() {
    wx.showToast({ title: '门诊挂号系统 v1.0.0', icon: 'none' });
  },
});
