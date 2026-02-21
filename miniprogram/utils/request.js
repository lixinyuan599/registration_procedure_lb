/**
 * wx.request 统一封装
 * 
 * 功能:
 * - 自动拼接 baseURL
 * - 自动携带 Authorization: Bearer <token>
 * - 统一处理响应格式和错误
 * - 401 时自动重新登录并重试
 * - 支持 loading 提示
 */

const BASE_URL = 'http://127.0.0.1:8000/api/v1';

/**
 * 发起请求
 * @param {Object} options - 请求配置
 * @param {string} options.url - 请求路径 (不含 baseURL)
 * @param {string} options.method - 请求方法 (GET/POST/PUT/DELETE)
 * @param {Object} options.data - 请求数据
 * @param {boolean} options.showLoading - 是否显示 loading (默认 true)
 * @param {boolean} options.noAuth - 是否跳过认证 (如 login 接口)
 * @param {boolean} options._isRetry - 是否为重试请求 (内部使用)
 * @returns {Promise}
 */
function request(options) {
  const {
    url, method = 'GET', data = {},
    showLoading = true, noAuth = false, _isRetry = false,
  } = options;
  const app = getApp();

  if (showLoading) {
    wx.showLoading({ title: '加载中...', mask: true });
  }

  // 构造请求头
  const header = { 'Content-Type': 'application/json' };
  if (!noAuth && app.globalData.token) {
    header['Authorization'] = `Bearer ${app.globalData.token}`;
  }
  // 多租户: 通过请求头传递 tenant_id
  if (app.globalData.tenantId) {
    header['X-Tenant-Id'] = String(app.globalData.tenantId);
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header,
      success(res) {
        if (showLoading) wx.hideLoading();

        // 401 未认证: 尝试重新登录后重试 (仅一次)
        if (res.statusCode === 401 && !_isRetry && !noAuth) {
          console.log('Token 过期，尝试重新登录...');
          app.login()
            .then(() => {
              // 重试原请求
              request({ ...options, _isRetry: true })
                .then(resolve)
                .catch(reject);
            })
            .catch((err) => {
              reject({ code: 401, message: '登录失败' });
            });
          return;
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          const body = res.data;
          if (body.code === 0) {
            resolve(body.data);
          } else {
            // 业务错误
            wx.showToast({
              title: body.message || '请求失败',
              icon: 'none',
              duration: 2000,
            });
            reject(body);
          }
        } else {
          // HTTP 错误
          const errMsg = res.data?.message || `请求失败 (${res.statusCode})`;
          wx.showToast({ title: errMsg, icon: 'none', duration: 2000 });
          reject({ code: res.statusCode, message: errMsg });
        }
      },
      fail(err) {
        if (showLoading) wx.hideLoading();
        wx.showToast({ title: '网络连接失败', icon: 'none', duration: 2000 });
        reject({ code: -1, message: err.errMsg || '网络错误' });
      },
    });
  });
}

// 快捷方法
function get(url, data, showLoading) {
  return request({ url, method: 'GET', data, showLoading });
}

function post(url, data, showLoading) {
  return request({ url, method: 'POST', data, showLoading });
}

function put(url, data, showLoading) {
  return request({ url, method: 'PUT', data, showLoading });
}

module.exports = { request, get, post, put };
