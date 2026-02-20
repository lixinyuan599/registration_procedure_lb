/**
 * 医生列表页
 * 展示某门店下所有在职医生
 */
const api = require('../../services/api');

Page({
  data: {
    clinicId: 0,
    clinicName: '',
    doctors: [],
    loading: true,
  },

  onLoad(options) {
    const clinicId = parseInt(options.clinicId);
    const clinicName = decodeURIComponent(options.clinicName || '');
    this.setData({ clinicId, clinicName });

    // 更新导航栏标题
    if (clinicName) {
      wx.setNavigationBarTitle({ title: clinicName });
    }

    this.loadDoctors(clinicId);
  },

  /**
   * 加载医生列表
   */
  async loadDoctors(clinicId) {
    this.setData({ loading: true });
    try {
      const doctors = await api.getDoctorsByClinic(clinicId);
      this.setData({ doctors, loading: false });
    } catch (err) {
      console.error('加载医生列表失败:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * 点击医生 -> 跳转排班页
   */
  onDoctorTap(e) {
    const doctor = e.currentTarget.dataset.doctor;
    wx.navigateTo({
      url: `/pages/doctor-schedule/doctor-schedule?doctorId=${doctor.id}&clinicId=${this.data.clinicId}&doctorName=${encodeURIComponent(doctor.name)}&expertise=${encodeURIComponent(doctor.expertise || '')}`,
    });
  },
});
