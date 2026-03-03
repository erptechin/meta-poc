import {
  apiAxiosWithToken,
} from "./apiHandler";
import {
  ADS,
  META_AD,
  REVOKE_ACCESS,
  GET_DATA,
  SET_DATA,
  RUN_META_ETL,
} from "./apis";

export const AdService = async (workspaceId) => {
  const res = await apiAxiosWithToken.get(`${ADS}${workspaceId}`);
  return res.data;
};

export const MetaService = async (data) => {
  const res = await apiAxiosWithToken.post(META_AD, data);
  return res.data;
};

export const DeleteIntegrationService = async (data) => {
  const res = await apiAxiosWithToken.post(REVOKE_ACCESS, data);
  return res.data;
};

export const GetDataService = async (workspaceId) => {
  const res = await apiAxiosWithToken.post(GET_DATA, { workspace_id: workspaceId });
  return res.data;
};

export const SetDataService = async (data) => {
  const res = await apiAxiosWithToken.post(SET_DATA, data);
  return res.data;
};

export const RunMetaEtlService = async (workspaceId) => {
  const res = await apiAxiosWithToken.post(RUN_META_ETL, { workspace_id: workspaceId });
  return res.data;
};