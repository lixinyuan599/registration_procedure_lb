const api = require('../../services/api');

Page({
  data: {
    clinicName: '',
    notice: '',
  },

  onLoad() {
    this._loadConfig();
  },

  onShow() {},

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
});
