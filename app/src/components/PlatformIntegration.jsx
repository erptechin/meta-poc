import React, { useMemo, useState, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { AdService, MetaService, GoogleService, DeleteIntegrationService } from "../services/platformService";
import "./PlatformIntegration.css";

const PLATFORM_CONFIG = {
    META: { name: "META", label: "Meta", icon: "🅼" },
    GOOGLE: { name: "GOOGLE", label: "Google", icon: "🅖" },
    LINKEDIN: { name: "LINKEDIN", label: "LinkedIn", icon: "🅛" },
};

const IntegratedView = React.memo(function IntegratedView({ item }) {
    const raw = item.ads_userinfo;
    const userInfo = raw?.userInfo ?? (raw && (raw.name || raw.email) ? raw : null);
    const pictureUrl = userInfo?.picture?.data?.url ?? (typeof userInfo?.picture === "string" ? userInfo.picture : null);
    const adAccounts = item.ads_accounts ?? raw?.adaccounts?.data ?? [];

    return (
        <div className="integrated-view">
            {userInfo && (
                <div className="integrated-view__user">
                    {pictureUrl && (
                        <img
                            src={pictureUrl}
                            alt=""
                            className="integrated-view__avatar"
                            width={40}
                            height={40}
                        />
                    )}
                    <div className="integrated-view__user-details">
                        <span className="integrated-view__user-name">{userInfo.name ?? userInfo.given_name}</span>
                        {(userInfo.email || userInfo.id) && (
                            <span className="integrated-view__user-email">{userInfo.email ?? userInfo.id}</span>
                        )}
                    </div>
                </div>
            )}
            {adAccounts.length > 0 && (
                <div className="integrated-view__accounts">
                    <span className="integrated-view__accounts-title">Ad accounts</span>
                    <ul className="integrated-view__accounts-list">
                        {adAccounts.map((acc, idx) => (
                            <li key={acc.id ?? acc.account_id ?? idx} className="integrated-view__account-item">
                                {acc.account_name ?? acc.name ?? acc.account_id}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
});

export default function PlatformIntegration() {
    const [deleteConfirmId, setDeleteConfirmId] = useState(null);

    const {
        data: adsData = [],
        refetch: adRefetch,
        isLoading,
        isError,
        error,
    } = useQuery({
        queryKey: ["all-ads"],
        queryFn: () => AdService(),
    });

    const platforms = useMemo(() => {
        const base = { ...PLATFORM_CONFIG };
        adsData.forEach((ad) => {
            if (ad.ad_platform in base) {
                base[ad.ad_platform] = {
                    ...base[ad.ad_platform],
                    ...ad,
                    isIntegrated: true,
                };
            }
        });
        return Object.values(base);
    }, [adsData]);

    const mutateMeta = useMutation({
        mutationFn: MetaService,
        onSuccess: (response) => {
            window.open(response.authUrl, "_blank", "popup,width=900,height=600");
            adRefetch();
        },
        onError: (err) => {
            console.error("Meta auth failed:", err);
        },
    });

    const mutateGoogle = useMutation({
        mutationFn: GoogleService,
        onSuccess: (response) => {
            window.open(response.authUrl, "_blank", "popup,width=900,height=600");
            adRefetch();
        },
        onError: (err) => {
            console.error("Google auth failed:", err);
        },
    });

    const mutateDelete = useMutation({
        mutationFn: DeleteIntegrationService,
        onSuccess: () => adRefetch(),
        onError: (err) => console.error("Delete failed:", err),
    });

    const handleAddAccount = useCallback((platformName) => {
        if (platformName === "META") {
            mutateMeta.mutate({});
        } else if (platformName === "GOOGLE") {
            mutateGoogle.mutate({});
        } else {
            toast.error(`Integration not supported for ${platformName}`);
        }
    }, [mutateMeta, mutateGoogle]);

    const handleDelete = useCallback((id) => {
        if (id == null) return;
        setDeleteConfirmId(id);
    }, []);

    const confirmDelete = useCallback(() => {
        if (deleteConfirmId == null) return;
        mutateDelete.mutate(
            { integration_id: deleteConfirmId },
            { onSettled: () => setDeleteConfirmId(null) }
        );
    }, [deleteConfirmId, mutateDelete]);

    const cancelDelete = useCallback(() => setDeleteConfirmId(null), []);

    if (isLoading) {
        return (
            <div className="platform-integration">
                <div className="platform-integration__loading">Loading platforms…</div>
            </div>
        );
    }

    if (isError) {
        return (
            <div className="platform-integration">
                <div className="platform-integration__error">
                    <h2>Platform Integration</h2>
                    <p>Failed to load: {error?.message || "Unknown error"}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="platform-integration">
            <h2 className="platform-integration__title">Platform Integration</h2>
            <p className="platform-integration__desc">
                Connect your ad platforms (Meta, Google, LinkedIn) to manage campaigns and sync data with your workspace.
            </p>
            <ul className="platform-list">
                {platforms.map((item) => (
                    <li
                        key={item.name}
                        className={`platform-list__row ${item.isIntegrated ? "platform-list__row--integrated" : ""}`}
                    >
                        <div className="platform-list__cell platform-list__cell--platform">
                            <span className="platform-list__icon" aria-hidden>{item.icon}</span>
                            <span className="platform-list__name">{item.label}</span>
                        </div>
                        <div className="platform-list__cell platform-list__cell--content">
                            {item.isIntegrated ? (
                                <IntegratedView item={item} />
                            ) : (
                                <span className="platform-list__empty">Not connected</span>
                            )}
                        </div>
                        <div className="platform-list__cell platform-list__cell--actions">
                            {item.isIntegrated ? (
                                <button
                                    type="button"
                                    className="platform-list__btn platform-list__btn--delete"
                                    onClick={() => handleDelete(item.id)}
                                    disabled={mutateDelete.isPending}
                                    title="Remove integration"
                                >
                                    {mutateDelete.isPending ? "Removing…" : "Delete"}
                                </button>
                            ) : (
                                <button
                                    type="button"
                                    className="platform-list__btn platform-list__btn--integrate"
                                    onClick={() => handleAddAccount(item.name)}
                                    disabled={mutateMeta.isPending || mutateGoogle.isPending}
                                >
                                    {(mutateMeta.isPending || mutateGoogle.isPending) ? "Connecting…" : "Integrate now"}
                                </button>
                            )}
                        </div>
                    </li>
                ))}
            </ul>

            {deleteConfirmId != null && (
                <div
                    className="delete-confirm-overlay"
                    onClick={cancelDelete}
                    onKeyDown={(e) => e.key === "Escape" && cancelDelete()}
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="delete-confirm-title"
                    tabIndex={0}
                >
                    <div
                        className="delete-confirm-dialog"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 id="delete-confirm-title" className="delete-confirm__title">
                            Remove integration?
                        </h3>
                        <p className="delete-confirm__message">
                            Are you sure you want to remove this integration? You can reconnect later.
                        </p>
                        <div className="delete-confirm__actions">
                            <button
                                type="button"
                                className="platform-list__btn platform-list__btn--integrate delete-confirm__btn"
                                onClick={cancelDelete}
                                disabled={mutateDelete.isPending}
                            >
                                No
                            </button>
                            <button
                                type="button"
                                className="platform-list__btn platform-list__btn--delete delete-confirm__btn"
                                onClick={confirmDelete}
                                disabled={mutateDelete.isPending}
                            >
                                {mutateDelete.isPending ? "Removing…" : "Yes"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
