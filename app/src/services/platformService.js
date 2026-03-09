import {
  apiAxiosWithToken,
} from "./apiHandler";
import {
  ADS,
  META_AD,
  GOOGLE_AD,
  REVOKE_ACCESS,
  GET_DATA,
  SET_DATA,
  RUN_META_ETL,
} from "./apis";

export const AdService = async () => {
  const res = await apiAxiosWithToken.get(ADS);
  return res.data;
};

export const MetaService = async (data) => {
  const res = await apiAxiosWithToken.post(META_AD, data);
  return res.data;
};

export const GoogleService = async (data) => {
  const res = await apiAxiosWithToken.post(GOOGLE_AD, data);
  return res.data;
};

export const DeleteIntegrationService = async (data) => {
  const res = await apiAxiosWithToken.post(REVOKE_ACCESS, data);
  return res.data;
};

export const GetDataService = async (workspaceId, { reportDate, reportDateFrom, reportDateTo } = {}) => {
  const body = { workspace_id: workspaceId };
  if (reportDate != null) body.report_date = reportDate;
  if (reportDateFrom != null) body.report_date_from = reportDateFrom;
  if (reportDateTo != null) body.report_date_to = reportDateTo;
  const res = await apiAxiosWithToken.post(GET_DATA, body);
  return res.data;
};

export const SetDataService = async (data) => {
  const res = await apiAxiosWithToken.post(SET_DATA, data);
  return res.data;
};

export const RunMetaEtlService = async (workspaceId, reportDate = null) => {
  const body = { workspace_id: workspaceId };
  if (reportDate != null) body.report_date = reportDate;
  const res = await apiAxiosWithToken.post(RUN_META_ETL, body);
  return res.data;
};