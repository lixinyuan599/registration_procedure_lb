const api = require('../../services/api');
const util = require('../../utils/util');
const app = getApp();

Page({
  data: {
    tenantName: '',
    tenantSubtitle: '',
    tenantLogo: '',
    notice: '',
    role: 'patient',
    doctorId: null,
  },

  onLoad() {
    this._loadTenantInfo();
  },

  onShow() {
    this.setData({
      role: app.globalData.role || 'patient',
      doctorId: app.globalData.doctorId || null,
    });
  },

  async _loadTenantInfo() {
    try {
      const tenant = await api.getCurrentTenant();
      if (tenant) {
        this.setData({
          tenantName: tenant.name || '门诊挂号',
          tenantSubtitle: tenant.subtitle || '',
          tenantLogo: tenant.logo_url ? util.fullImageUrl(tenant.logo_url) : '',
        });
      }
    } catch (e) {
      console.log('加载企业信息失败', e);
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
