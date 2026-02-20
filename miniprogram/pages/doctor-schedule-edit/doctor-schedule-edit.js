/**
 * 医生排班编辑页
 *
 * 功能:
 *  - 顶部门店选择器 (支持多门店医生切换)
 *  - 三个 Tab: 排班模板 / 本周排班 / 下周排班
 *  - 每个 Tab 内是 7天 x 2时段 网格，支持开关
 */
const api = require('../../services/api');
const app = getApp();

const WEEKDAY_LABELS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

/**
 * 计算指定周的日期范围
 */
function getWeekDates(week) {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
  const monday = new Date(now);
  monday.setDate(now.getDate() + mondayOffset);
  if (week === 'next') {
    monday.setDate(monday.getDate() + 7);
  }

  const dates = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const dateStr = `${d.getFullYear()}-${mm}-${dd}`;
    dates.push({
      date: dateStr,
      weekday: i,
      label: WEEKDAY_LABELS[i],
      dateLabel: `${mm}/${dd}`,
    });
  }
  return dates;
}

Page({
  data: {
    isDoctor: false,
    doctorId: null,
    loading: true,
    saving: false,
    generating: false,
    maxPatients: 20,

    // 门店选择器
    doctorClinics: [],     // [{id, name}]
    selectedClinicIdx: 0,  // picker 选中索引
    selectedClinicId: null, // 当前选中门店 ID

    // Tab
    activeTab: 0,
    tabs: [
      { name: '排班模板', key: 'template' },
      { name: '本周排班', key: 'current' },
      { name: '下周排班', key: 'next' },
    ],

    // 排班模板数据
    weekDays: [],

    // 本周/下周排班数据
    currentWeekDays: [],
    nextWeekDays: [],
    currentWeekRange: '',
    nextWeekRange: '',
  },

  onLoad() {
    const role = app.globalData.role;
    const doctorId = app.globalData.doctorId;

    if (role === 'doctor' && doctorId) {
      this.setData({ isDoctor: true, doctorId });
      this._loadDoctorClinics(doctorId);
    } else {
      this.setData({ isDoctor: false, loading: false });
    }
  },

  onShow() {
    const role = app.globalData.role;
    const doctorId = app.globalData.doctorId;
    if (role === 'doctor' && doctorId && !this.data.isDoctor) {
      this.setData({ isDoctor: true, doctorId });
      this._loadDoctorClinics(doctorId);
    }
  },

  /**
   * 加载医生关联的门店列表，然后初始化排班数据
   */
  async _loadDoctorClinics(doctorId) {
    this.setData({ loading: true });
    try {
      const clinics = await api.getDoctorClinics(doctorId);
      if (clinics && clinics.length > 0) {
        this.setData({
          doctorClinics: clinics,
          selectedClinicIdx: 0,
          selectedClinicId: clinics[0].id,
        });
        await this._initAllTabs(doctorId, clinics[0].id);
      } else {
        this.setData({ doctorClinics: [], selectedClinicId: null });
        await this._initAllTabs(doctorId, null);
      }
    } catch (e) {
      console.error('加载门店列表失败:', e);
      await this._initAllTabs(doctorId, null);
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
      this._initAllTabs(this.data.doctorId, clinic.id);
    }
  },

  /**
   * 初始化所有 Tab 数据
   */
  async _initAllTabs(doctorId, clinicId) {
    this.setData({ loading: true });
    try {
      await Promise.all([
        this.loadTemplate(doctorId, clinicId),
        this.loadWeekSchedule(doctorId, 'current', clinicId),
        this.loadWeekSchedule(doctorId, 'next', clinicId),
      ]);
    } catch (e) {
      console.error('初始化排班数据失败:', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  /**
   * 切换 Tab
   */
  onSwitchTab(e) {
    const idx = parseInt(e.currentTarget.dataset.idx, 10);
    this.setData({ activeTab: idx });
  },

  // ========== 排班模板 (Tab 0) ==========

  async loadTemplate(doctorId, clinicId) {
    try {
      const templates = await api.getDoctorTemplate(doctorId, clinicId);
      this._applyTemplates(templates || []);
    } catch (err) {
      console.error('加载排班模板失败:', err);
      this._applyTemplates([]);
    }
  },

  _applyTemplates(templates) {
    const weekDays = [];
    let maxP = 20;

    for (let i = 0; i < 7; i++) {
      const dayTemplates = templates.filter(t => t.weekday === i);
      let morning = false;
      let afternoon = false;

      for (const t of dayTemplates) {
        const hour = parseInt(t.start_time.split(':')[0], 10);
        if (hour < 12) morning = true;
        else afternoon = true;
        if (t.max_patients) maxP = t.max_patients;
      }

      weekDays.push({
        weekday: i,
        label: WEEKDAY_LABELS[i],
        morning,
        afternoon,
      });
    }

    this.setData({ weekDays, maxPatients: maxP });
  },

  onToggleSlot(e) {
    const { weekday, period } = e.currentTarget.dataset;
    const weekDays = this.data.weekDays.slice();
    const idx = weekDays.findIndex(d => d.weekday === weekday);
    if (idx >= 0) {
      weekDays[idx][period] = !weekDays[idx][period];
      this.setData({ weekDays });
    }
  },

  onDecreasePatients() {
    const v = this.data.maxPatients;
    if (v > 1) this.setData({ maxPatients: v - 1 });
  },

  onIncreasePatients() {
    const v = this.data.maxPatients;
    if (v < 99) this.setData({ maxPatients: v + 1 });
  },

  async onSaveTemplate() {
    if (this.data.saving) return;
    this.setData({ saving: true });

    const slots = [];
    const maxP = this.data.maxPatients;

    for (const day of this.data.weekDays) {
      if (day.morning) {
        slots.push({
          weekday: day.weekday,
          start_time: '09:00:00',
          end_time: '12:00:00',
          max_patients: maxP,
          is_active: true,
        });
      }
      if (day.afternoon) {
        slots.push({
          weekday: day.weekday,
          start_time: '14:00:00',
          end_time: '17:00:00',
          max_patients: maxP,
          is_active: true,
        });
      }
    }

    try {
      await api.updateDoctorTemplate(this.data.doctorId, slots, this.data.selectedClinicId);
      wx.showToast({ title: '保存成功', icon: 'success' });
    } catch (err) {
      console.error('保存排班模板失败:', err);
    } finally {
      this.setData({ saving: false });
    }
  },

  async onGenerateSchedules() {
    if (this.data.generating) return;

    const res = await new Promise(resolve => {
      wx.showModal({
        title: '生成排班',
        content: '将根据当前模板生成下一周的排班，已有排班不会重复创建。确认继续？',
        success: resolve,
      });
    });
    if (!res.confirm) return;

    this.setData({ generating: true });
    try {
      const result = await api.generateSchedules(1, this.data.doctorId);
      wx.showToast({
        title: `已生成 ${result.created} 条`,
        icon: 'success',
        duration: 2000,
      });
      const cid = this.data.selectedClinicId;
      await this.loadWeekSchedule(this.data.doctorId, 'current', cid);
      await this.loadWeekSchedule(this.data.doctorId, 'next', cid);
    } catch (err) {
      console.error('生成排班失败:', err);
    } finally {
      this.setData({ generating: false });
    }
  },

  // ========== 本周/下周排班 (Tab 1 & 2) ==========

  async loadWeekSchedule(doctorId, week, clinicId) {
    try {
      const resp = await api.getWeekSchedules(doctorId, week, clinicId);
      const dates = getWeekDates(week);
      const schedules = resp.schedules || [];

      const weekDays = dates.map(d => {
        const daySchedules = schedules.filter(s => s.date === d.date);
        let morning = false;
        let afternoon = false;
        let morningStatus = '';
        let afternoonStatus = '';
        let morningPatients = 0;
        let afternoonPatients = 0;

        for (const s of daySchedules) {
          const hour = parseInt(s.start_time.split(':')[0], 10);
          if (hour < 12) {
            morning = s.status !== 'closed';
            morningStatus = s.status;
            morningPatients = s.current_patients;
          } else {
            afternoon = s.status !== 'closed';
            afternoonStatus = s.status;
            afternoonPatients = s.current_patients;
          }
        }

        return {
          ...d,
          morning,
          afternoon,
          morningStatus,
          afternoonStatus,
          morningPatients,
          afternoonPatients,
        };
      });

      const rangeStr = `${resp.date_from} ~ ${resp.date_to}`;

      if (week === 'current') {
        this.setData({ currentWeekDays: weekDays, currentWeekRange: rangeStr });
      } else {
        this.setData({ nextWeekDays: weekDays, nextWeekRange: rangeStr });
      }
    } catch (err) {
      console.error(`加载${week === 'current' ? '本周' : '下周'}排班失败:`, err);
      const dates = getWeekDates(week);
      const emptyDays = dates.map(d => ({
        ...d,
        morning: false,
        afternoon: false,
        morningStatus: '',
        afternoonStatus: '',
        morningPatients: 0,
        afternoonPatients: 0,
      }));
      if (week === 'current') {
        this.setData({ currentWeekDays: emptyDays, currentWeekRange: '' });
      } else {
        this.setData({ nextWeekDays: emptyDays, nextWeekRange: '' });
      }
    }
  },

  onToggleWeekSlot(e) {
    const { week, idx, period } = e.currentTarget.dataset;
    const key = week === 'current' ? 'currentWeekDays' : 'nextWeekDays';
    const weekDays = this.data[key].slice();
    const i = parseInt(idx, 10);
    if (i >= 0 && i < weekDays.length) {
      weekDays[i] = { ...weekDays[i] };
      weekDays[i][period] = !weekDays[i][period];
      this.setData({ [key]: weekDays });
    }
  },

  async onSaveWeekSchedule(e) {
    const week = e.currentTarget.dataset.week;
    if (this.data.saving) return;
    this.setData({ saving: true });

    const key = week === 'current' ? 'currentWeekDays' : 'nextWeekDays';
    const weekDays = this.data[key];
    const maxP = this.data.maxPatients;

    const slots = [];
    for (const day of weekDays) {
      slots.push({
        date: day.date,
        start_time: '09:00:00',
        end_time: '12:00:00',
        is_open: !!day.morning,
        max_patients: maxP,
      });
      slots.push({
        date: day.date,
        start_time: '14:00:00',
        end_time: '17:00:00',
        is_open: !!day.afternoon,
        max_patients: maxP,
      });
    }

    try {
      await api.updateWeekSchedules(this.data.doctorId, week, slots, this.data.selectedClinicId);
      wx.showToast({ title: '保存成功', icon: 'success' });
      await this.loadWeekSchedule(this.data.doctorId, week, this.data.selectedClinicId);
    } catch (err) {
      console.error('保存排班失败:', err);
      wx.showToast({ title: '保存失败', icon: 'none' });
    } finally {
      this.setData({ saving: false });
    }
  },
});
