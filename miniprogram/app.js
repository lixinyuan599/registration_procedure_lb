/**
 * 门诊挂号小程序 - 全局入口
 */
const api = require('./services/api');

/**
 * 开发模式配置
 * DEV_MODE = true 时使用固定 openid 登录，避免每次 wx.login() 生成新用户
 * 发布上线前务必设为 false
 */
const DEV_MODE = true;
const DEV_OPENID = 'dev_doctor_001';  // 开发用固定 openid，可按需切换

App({
  globalData: {
    // 用户身份信息 (登录后填充)
    token: '',
    openid: '',
    role: 'patient',   // patient / doctor / admin
    doctorId: null,     // 医生关联 ID (仅 role=doctor 时有值)
    userInfo: null,
    // 登录状态 Promise (防止并发重复登录)
    loginPromise: null,
    // 当前选中的门店
    selectedClinic: null,
  },

  onLaunch() {
    console.log('小程序启动');
    // 尝试从缓存恢复登录态
    const token = wx.getStorageSync('token');
    const openid = wx.getStorageSync('openid');
    const role = wx.getStorageSync('role');
    const doctorId = wx.getStorageSync('doctorId');
    if (token && openid) {
      this.globalData.token = token;
      this.globalData.openid = openid;
      this.globalData.role = role || 'patient';
      this.globalData.doctorId = doctorId || null;
      console.log('从缓存恢复登录态, role:', role);
    } else {
      // 无缓存，发起登录
      this.login();
    }
  },

  /**
   * 微信登录
   * 返回 Promise，可 await
   */
  login() {
    // 防止并发重复登录
    if (this.globalData.loginPromise) {
      return this.globalData.loginPromise;
    }

    this.globalData.loginPromise = new Promise((resolve, reject) => {
      // 开发模式: 使用固定 openid，不走 wx.login
      if (DEV_MODE) {
        console.log('[DEV] 使用固定 openid:', DEV_OPENID);
        api.login(DEV_OPENID)
          .then((data) => {
            this.globalData.token = data.token;
            this.globalData.openid = data.openid;
            this.globalData.role = data.role || 'patient';
            this.globalData.doctorId = data.doctor_id || null;
            wx.setStorageSync('token', data.token);
            wx.setStorageSync('openid', data.openid);
            wx.setStorageSync('role', data.role || 'patient');
            wx.setStorageSync('doctorId', data.doctor_id || null);
            console.log('[DEV] 登录成功, role:', data.role, 'doctor_id:', data.doctor_id);
            resolve(data);
          })
          .catch((err) => {
            console.error('[DEV] 登录失败:', err);
            reject(err);
          })
          .finally(() => {
            this.globalData.loginPromise = null;
          });
        return;
      }

      wx.login({
        success: (res) => {
          if (res.code) {
            console.log('wx.login code:', res.code);
            // 发送 code 到后端换取 token
            api.login(res.code)
              .then((data) => {
                this.globalData.token = data.token;
                this.globalData.openid = data.openid;
                this.globalData.role = data.role || 'patient';
                this.globalData.doctorId = data.doctor_id || null;
                // 持久化到本地缓存
                wx.setStorageSync('token', data.token);
                wx.setStorageSync('openid', data.openid);
                wx.setStorageSync('role', data.role || 'patient');
                wx.setStorageSync('doctorId', data.doctor_id || null);
                console.log('登录成功, openid:', data.openid, 'role:', data.role);
                resolve(data);
              })
              .catch((err) => {
                console.error('后端登录失败:', err);
                reject(err);
              })
              .finally(() => {
                this.globalData.loginPromise = null;
              });
          } else {
            console.error('wx.login 失败:', res.errMsg);
            this.globalData.loginPromise = null;
            reject(new Error(res.errMsg));
          }
        },
        fail: (err) => {
          console.error('wx.login 调用失败:', err);
          this.globalData.loginPromise = null;
          reject(err);
        },
      });
    });

    return this.globalData.loginPromise;
  },

  /**
   * 确保已登录 (供页面调用)
   * 如果已有 token 直接返回，否则等待登录完成
   */
  ensureLogin() {
    if (this.globalData.token) {
      return Promise.resolve();
    }
    return this.login();
  },
});
