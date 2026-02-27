const api = require('../../services/api');
const util = require('../../utils/util');

Page({
  data: {
    doctors: [],
    loading: true,
    searchText: '',
  },

  _searchTimer: null,

  onLoad() {
    this.loadDoctors();
  },

  async loadDoctors(search) {
    this.setData({ loading: true });
    try {
      const doctors = await api.getAllDoctors(search || '');
      doctors.forEach(d => { d.avatar_url = util.fullImageUrl(d.avatar_url); });
      this.setData({ doctors, loading: false });
    } catch (e) {
      console.error('加载医生列表失败:', e);
      this.setData({ doctors: [], loading: false });
    }
  },

  onSearchInput(e) {
    const value = e.detail.value;
    this.setData({ searchText: value });

    // 防抖搜索 (500ms)
    if (this._searchTimer) clearTimeout(this._searchTimer);
    this._searchTimer = setTimeout(() => {
      this.loadDoctors(value);
    }, 500);
  },

  onSearch() {
    if (this._searchTimer) clearTimeout(this._searchTimer);
    this.loadDoctors(this.data.searchText);
  },

  onClearSearch() {
    this.setData({ searchText: '' });
    this.loadDoctors('');
  },

  onDoctorTap(e) {
    const doctor = e.currentTarget.dataset.doctor;
    wx.navigateTo({
      url: `/pages/doctor-schedule/doctor-schedule?doctorId=${doctor.id}&doctorName=${encodeURIComponent(doctor.name)}&expertise=${encodeURIComponent(doctor.expertise || '')}`,
    });
  },
});
