/**
 * 打刻時の位置情報を取得する（詳細設計書 7.9）
 * 許可されていない・取得できない・5秒でタイムアウトした場合は空のオブジェクトを返し、位置なしで打刻する。
 */
export type PunchLocation = { latitude?: number; longitude?: number }

export function getPunchLocation(timeoutMs = 5000): Promise<PunchLocation> {
  if (typeof navigator === 'undefined' || !navigator.geolocation) return Promise.resolve({})
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
      () => resolve({}),
      { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 60_000 },
    )
  })
}
