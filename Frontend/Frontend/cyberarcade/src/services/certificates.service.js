import { api, BASE_URL, getAccessToken } from "./api";

export const certificatesService = {
  /** All certificates for the logged-in user. */
  myCertificates: () => api.get("/api/certificates/me"),

  /** Check if user has completed a course + whether a cert already exists. */
  completionStatus: (courseId) =>
    api.get(`/api/certificates/completion/${courseId}`),

  /** Generate (or fetch existing) certificate for a completed course. */
  generate: (courseId) => api.post(`/api/certificates/generate/${courseId}`),

  /** Public serial verification — no auth required. */
  verify: (serial) => api.get(`/api/certificates/verify/${serial}`),

  /** Returns the download URL for a certificate PDF. */
  downloadUrl: (certId) =>
    `${BASE_URL}/api/certificates/${certId}/download`,

  /** Trigger browser download of the PDF. */
  download(certId, serial) {
    const token = getAccessToken();
    const url = `${BASE_URL}/api/certificates/${certId}/download`;
    return fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        if (!res.ok) throw new Error("Download failed");
        return res.blob();
      })
      .then((blob) => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `CyberArcade_Certificate_${serial}.pdf`;
        a.click();
        URL.revokeObjectURL(a.href);
      });
  },

  /** Open the PDF in a new browser tab. */
  view(certId) {
    const token = getAccessToken();
    const url = `${BASE_URL}/api/certificates/${certId}/download`;
    return fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then((res) => {
        if (!res.ok) throw new Error("View failed");
        return res.blob();
      })
      .then((blob) => {
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        a.click();
        setTimeout(() => URL.revokeObjectURL(blobUrl), 30000);
      });
  },

  /** Admin: list all certificates. */
  adminList: () => api.get("/api/certificates/admin/all"),

  /** Admin: revoke a certificate. */
  adminRevoke: (certId) => api.put(`/api/certificates/admin/${certId}/revoke`),
};
