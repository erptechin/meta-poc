import {
  apiAxiosWithToken,
} from "./apiHandler";
import {
  ADS,
  META_AD,
  REVOKE_ACCESS,
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