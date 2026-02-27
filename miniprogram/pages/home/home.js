const api = require('../../services/api');
const app = getApp();

Page({
  data: {
    clinicName: '',
    notice: '',
    role: 'patient',
    doctorId: null,
  },

  onLoad() {
    this._loadConfig();
  },

  onShow() {
    this.setData({
      role: app.globalData.role || 'patient',
      doctorId: app.globalData.doctorId || null,
    });
  },

  async _loadConfig() {
    try {
      const config = await api.getDisplayConfig();
      if (config && config.clinic_name) {
        this.setData({ clinicName: config.clinic_name });
      }
    } catch (e) {
      console.log('加载配置失败', e);
    }
  },

  /** 按门店挂号 */
  goClinicList() {
    wx.navigateTo({ url: '/pages/clinic-list/clinic-list' });
  },

  /** 按医生挂号 */
  goDoctorAll() {
    wx.navigateTo({ url: '/pages/doctor-all/doctor-all' });
  },

  /** 辅助诊断 */
  goDiagnosis() {
    wx.navigateTo({ url: '/pages/diagnosis/diagnosis' });
  },

  /** 挂号列表 (医生) */
  goDoctorQueue() {
    wx.navigateTo({ url: '/pages/doctor-queue/doctor-queue' });
  },

  /** 排班管理 (医生) */
  goScheduleEdit() {
    wx.navigateTo({ url: '/pages/doctor-schedule-edit/doctor-schedule-edit' });
  },
});
