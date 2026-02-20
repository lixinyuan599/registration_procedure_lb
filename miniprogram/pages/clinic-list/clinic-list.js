/**
 * 门店选择页
 * 从首页「按门店挂号」入口进入
 */
const api = require('../../services/api');

Page({
  data: {
    clinics: [],
    loading: true,
  },

  onLoad() {
    this.loadClinics();
  },

  onPullDownRefresh() {
    this.loadClinics().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 加载门店列表
   */
  async loadClinics() {
    this.setData({ loading: true });
    try {
      const clinics = await api.getClinics();
      this.setData({ clinics, loading: false });
    } catch (err) {
      console.error('加载门店失败:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * 点击门店 -> 跳转医生列表页
   */
  onClinicTap(e) {
    const clinic = e.currentTarget.dataset.clinic;
    // 存入全局数据
    const app = getApp();
    app.globalData.selectedClinic = clinic;

    wx.navigateTo({
      url: `/pages/doctor-list/doctor-list?clinicId=${clinic.id}&clinicName=${encodeURIComponent(clinic.name)}`,
    });
  },
});
