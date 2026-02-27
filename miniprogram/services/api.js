/**
 * API 接口层 - 统一管理所有后端 API 调用
 */

const http = require('../utils/request');

/** ========== 认证 API ========== */

/**
 * 微信登录
 * @param {string} code - wx.login() 获取的 code
 */
function login(code) {
  return http.request({
    url: '/auth/login',
    method: 'POST',
    data: { code },
    noAuth: true,  // 登录接口不需要 token
    showLoading: false,
  });
}

/** ========== 门店 API ========== */

/**
 * 获取门店列表
 */
function getClinics() {
  return http.get('/clinics');
}

/**
 * 获取门店详情
 */
function getClinicDetail(clinicId) {
  return http.get(`/clinics/${clinicId}`);
}

/** ========== 医生 API ========== */

/**
 * 获取全部在职医生列表 (跨门店)
 * @param {string} search - 搜索关键词 (可选)
 */
function getAllDoctors(search) {
  const params = {};
  if (search) params.search = search;
  return http.get('/doctors', params);
}

/**
 * 获取门店的医生列表
 */
function getDoctorsByClinic(clinicId) {
  return http.get(`/clinics/${clinicId}/doctors`);
}

/**
 * 获取医生关联的门店列表
 * @param {number} doctorId - 医生 ID
 * @returns {Promise<Array<{id: number, name: string}>>}
 */
function getDoctorClinics(doctorId) {
  return http.get(`/doctors/${doctorId}/clinics`);
}

/** ========== 排班 API ========== */

/**
 * 获取医生排班
 * @param {number} doctorId - 医生 ID
 * @param {string} dateFrom - 起始日期 (可选)
 * @param {string} dateTo - 结束日期 (可选)
 */
function getDoctorSchedules(doctorId, dateFrom, dateTo, clinicId) {
  const params = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  if (clinicId) params.clinic_id = clinicId;
  return http.get(`/doctors/${doctorId}/schedules`, params);
}

/** ========== 预约 API ========== */

/**
 * 创建预约
 * @param {Object} data - { doctor_id, clinic_id, schedule_id, notes }
 */
function createAppointment(data) {
  return http.post('/appointments', data);
}

/**
 * 获取我的预约列表
 */
function getMyAppointments() {
  return http.get('/appointments/me');
}

/**
 * 取消预约
 */
function cancelAppointment(appointmentId) {
  return http.put(`/appointments/${appointmentId}/cancel`);
}

/** ========== 排班模板 API ========== */

/**
 * 获取医生的周排班模板
 * @param {number} doctorId - 医生 ID
 * @param {number|null} clinicId - 门店 ID (可选, 按门店过滤)
 */
function getDoctorTemplate(doctorId, clinicId) {
  let url = `/doctors/${doctorId}/schedule-template`;
  if (clinicId) url += `?clinic_id=${clinicId}`;
  return http.get(url);
}

/**
 * 更新医生的周排班模板
 * @param {number} doctorId - 医生 ID
 * @param {Array} slots - 模板时段数组
 * @param {number|null} clinicId - 门店 ID (可选)
 */
function updateDoctorTemplate(doctorId, slots, clinicId) {
  let url = `/doctors/${doctorId}/schedule-template`;
  if (clinicId) url += `?clinic_id=${clinicId}`;
  return http.put(url, { slots });
}

/**
 * 根据模板生成排班
 * @param {number} weeks - 生成周数
 * @param {number|null} doctorId - 医生 ID (可选)
 */
function generateSchedules(weeks, doctorId) {
  let url = `/schedules/generate?weeks=${weeks || 1}`;
  if (doctorId) url += `&doctor_id=${doctorId}`;
  return http.post(url);
}

/** ========== 周排班编辑 API ========== */

/**
 * 获取医生本周或下周排班
 * @param {number} doctorId - 医生 ID
 * @param {'current'|'next'} week - 本周或下周
 * @param {number|null} clinicId - 门店 ID (可选)
 */
function getWeekSchedules(doctorId, week, clinicId) {
  let url = `/doctors/${doctorId}/week-schedules/${week}`;
  if (clinicId) url += `?clinic_id=${clinicId}`;
  return http.get(url);
}

/**
 * 修改医生本周或下周排班
 * @param {number} doctorId - 医生 ID
 * @param {'current'|'next'} week - 本周或下周
 * @param {Array} slots - 排班时段数组
 * @param {number|null} clinicId - 门店 ID (可选)
 */
function updateWeekSchedules(doctorId, week, slots, clinicId) {
  let url = `/doctors/${doctorId}/week-schedules/${week}`;
  if (clinicId) url += `?clinic_id=${clinicId}`;
  return http.put(url, { slots });
}

/** ========== 用户 API ========== */

/**
 * 获取当前用户信息 (角色、医生绑定状态等)
 */
function getMyProfile() {
  return http.get('/users/me');
}

/**
 * 通过邀请码绑定医生身份
 * @param {string} inviteCode - 管理员提供的邀请码
 */
function bindDoctor(inviteCode) {
  return http.post('/users/bind-doctor', { invite_code: inviteCode });
}

/**
 * 解除医生身份绑定
 */
function unbindDoctor() {
  return http.post('/users/unbind-doctor');
}

/** ========== 系统配置 API ========== */

/**
 * 获取显示配置
 * @returns {Promise<{show_remaining_slots: boolean, clinic_name: string}>}
 */
function getDisplayConfig() {
  return http.get('/config/display', {}, false);
}

module.exports = {
  login,
  getClinics,
  getClinicDetail,
  getAllDoctors,
  getDoctorsByClinic,
  getDoctorClinics,
  getDoctorSchedules,
  createAppointment,
  getMyAppointments,
  cancelAppointment,
  getDoctorTemplate,
  updateDoctorTemplate,
  generateSchedules,
  getWeekSchedules,
  updateWeekSchedules,
  getDisplayConfig,
  getMyProfile,
  bindDoctor,
  unbindDoctor,
};
