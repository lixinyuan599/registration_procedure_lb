/**
 * 医生排班页
 * 展示某医生的排班时段，用户选择后进入预约确认
 * 支持按门店筛选排班
 */
const api = require('../../services/api');
const util = require('../../utils/util');

Page({
  data: {
    doctorId: 0,
    clinicId: 0,            // 进入页面时的门店 (来自上一页传参)
    doctorName: '',
    expertise: '',
    schedules: [],
    groupedSchedules: [],
    loading: true,
    showRemaining: true,

    // 门店选择器
    doctorClinics: [],       // 医生关联的所有门店
    selectedClinicIdx: 0,
    selectedClinicId: 0,
    hasMultiClinics: false,
  },

  onLoad(options) {
    const doctorId = parseInt(options.doctorId);
    const clinicId = parseInt(options.clinicId);
    const doctorName = decodeURIComponent(options.doctorName || '');
    const expertise = decodeURIComponent(options.expertise || '');

    this.setData({ doctorId, clinicId, doctorName, expertise, selectedClinicId: clinicId });
    this.loadDisplayConfig();
    this._loadDoctorClinics(doctorId, clinicId);
  },

  async loadDisplayConfig() {
    try {
      const config = await api.getDisplayConfig();
      if (config) {
        this.setData({ showRemaining: config.show_remaining_slots !== false });
      }
    } catch (err) {
      console.log('加载显示配置失败，使用默认值');
    }
  },

  /**
   * 加载医生关联门店，然后加载排班
   */
  async _loadDoctorClinics(doctorId, currentClinicId) {
    try {
      const clinics = await api.getDoctorClinics(doctorId);
      if (clinics && clinics.length > 0) {
        // 找到当前门店在列表中的索引
        let idx = clinics.findIndex(c => c.id === currentClinicId);
        if (idx < 0) idx = 0;

        this.setData({
          doctorClinics: clinics,
          selectedClinicIdx: idx,
          selectedClinicId: clinics[idx].id,
          hasMultiClinics: clinics.length > 1,
        });
        this.loadSchedules(doctorId, clinics[idx].id);
      } else {
        this.setData({ doctorClinics: [], hasMultiClinics: false });
        this.loadSchedules(doctorId, null);
      }
    } catch (err) {
      console.error('加载医生门店列表失败:', err);
      this.loadSchedules(doctorId, currentClinicId);
    }
  },

  /**
   * 切换门店
   */
  onClinicChange(e) {
    const idx = parseInt(e.detail.value, 10);
    const clinic = this.data.doctorClinics[idx];
    if (clinic) {
      this.setData({
        selectedClinicIdx: idx,
        selectedClinicId: clinic.id,
      });
      this.loadSchedules(this.data.doctorId, clinic.id);
    }
  },

  /**
   * 加载排班数据
   */
  async loadSchedules(doctorId, clinicId) {
    this.setData({ loading: true });
    try {
      const schedules = await api.getDoctorSchedules(doctorId, null, null, clinicId);
      const groupedSchedules = this.groupByDate(schedules);
      this.setData({ schedules, groupedSchedules, loading: false });
    } catch (err) {
      console.error('加载排班失败:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * 按日期分组排班数据
   */
  groupByDate(schedules) {
    const map = {};
    schedules.forEach((s) => {
      const dateKey = s.date;
      if (!map[dateKey]) {
        map[dateKey] = {
          date: dateKey,
          dateLabel: util.friendlyDate(dateKey),
          slots: [],
        };
      }
      map[dateKey].slots.push({
        ...s,
        timeLabel: `${util.formatTime(s.start_time)} - ${util.formatTime(s.end_time)}`,
        remaining: s.max_patients - s.current_patients,
        isAvailable: s.status === 'open' && s.current_patients < s.max_patients,
      });
    });
    return Object.values(map);
  },

  /**
   * 点击时段 -> 跳转预约确认页
   */
  onSlotTap(e) {
    const slot = e.currentTarget.dataset.slot;
    if (!slot.isAvailable) {
      wx.showToast({ title: '该时段已约满', icon: 'none' });
      return;
    }

    // 使用当前选中的门店
    const clinicId = this.data.selectedClinicId || this.data.clinicId;

    wx.navigateTo({
      url: `/pages/appointment-confirm/appointment-confirm?scheduleId=${slot.id}&doctorId=${this.data.doctorId}&clinicId=${clinicId}&doctorName=${encodeURIComponent(this.data.doctorName)}&expertise=${encodeURIComponent(this.data.expertise)}&date=${slot.date}&timeSlot=${encodeURIComponent(slot.timeLabel)}&remaining=${slot.remaining}`,
    });
  },
});
