import React, { useMemo, useState, useEffect } from "react";
import { useGuiState } from "./001_GuiStateProvider";
import { isDesktopApp } from "../../const";
import { useAppRoot } from "../../001_provider/001_AppRootProvider";
import { useMessageBuilder } from "../../hooks/useMessageBuilder";

function isRunningInWebView(): boolean {
    const params = new URLSearchParams(window.location.search);
    const isInWebview = params.has("webview");
    return isInWebview;
}

export const StartingNoticeDialog = () => {
    const guiState = useGuiState();
    const { appGuiSettingState } = useAppRoot();
    const messageBuilderState = useMessageBuilder();

    const [needsPassword, setNeedsPassword] = useState(false);
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    useEffect(() => {
        if (!isRunningInWebView()) {
            setNeedsPassword(true);
        }
    }, []);

    useMemo(() => {
        messageBuilderState.setMessage(__filename, "support", { ja: "支援", en: "Donation" });
        messageBuilderState.setMessage(__filename, "support_message_1", { ja: "このソフトウェアを気に入ったら開発者にコーヒーをご馳走してあげよう。黄色いアイコンから。", en: "This software is supported by donations. Thank you for your support!" });
        messageBuilderState.setMessage(__filename, "support_message_2", { ja: "コーヒーをご馳走する。", en: "I will support a developer by buying coffee." });
        messageBuilderState.setMessage(__filename, "directml_1", { ja: "directML版は実験的バージョンです。以下の既知の問題があります。", en: "DirectML version is an experimental version. There are the known issues as follows." });
        messageBuilderState.setMessage(__filename, "directml_2", {
            ja: "(1) 一部の設定変更を行うとgpuを使用していても変換処理が遅くなることが発生します。もしこの現象が発生したらGPUの値を-1にしてから再度0に戻してください。",
            en: "(1) When some settings are changed, conversion process becomes slow even when using GPU. If this occurs, reset the GPU value to -1 and then back to 0.",
        });
        messageBuilderState.setMessage(__filename, "web_edditon_1", { ja: "このWebエディションは実験的バージョンです。", en: "This edition(web) is an experimental Edition." });
        messageBuilderState.setMessage(__filename, "web_edditon_2", {
            ja: "より高機能・高性能なFullエディションは、",
            en: "The more advanced and high-performance Full Edition can be obtained for free from the following GitHub repository.",
        });
        messageBuilderState.setMessage(__filename, "web_edditon_3", {
            ja: "次のgithubリポジトリから無料で取得できます。",
            en: "",
        });
        messageBuilderState.setMessage(__filename, "github", { ja: "github", en: "github" });
        messageBuilderState.setMessage(__filename, "click_to_start", { ja: "スタートボタンを押してください。", en: "Click to start" });
        messageBuilderState.setMessage(__filename, "start", { ja: "スタート", en: "start" });
    }, []);

    const handleStartClick = () => {
        if (needsPassword) {
            if (password === "1234") {
                guiState.stateControls.showStartingNoticeCheckbox.updateState(false);
            } else {
                setError("Contraseña incorrecta");
            }
        } else {
            guiState.stateControls.showStartingNoticeCheckbox.updateState(false);
        }
    };

    const dialog = useMemo(() => {
        const donationMessage = (
            <div className="dialog-content-part">
                <div>{messageBuilderState.getMessage(__filename, "support_message_1")}</div>
            </div>
        );

        const licenseInfo = <div className="dialog-content-part">License Notice</div>;

        const clickToStartMessage = (
            <div className="dialog-content-part">
                <div>{messageBuilderState.getMessage(__filename, "click_to_start")}</div>
            </div>
        );

        return (
            <div className="dialog-frame">
                <div className="dialog-title">HuSa.IA</div>
                <div className="dialog-content">
                    {needsPassword && (
                        <div className="dialog-content-part">
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Contraseña"
                            />
                            {error && <p style={{ color: "red" }}>{error}</p>}
                        </div>
                    )}

                    <div className="body-row split-3-4-3 left-padding-1">
                        <div className="body-item-text"></div>
                        <div className="body-button-container body-button-container-space-around">
                            <div className="body-button" onClick={handleStartClick}>
                                {messageBuilderState.getMessage(__filename, "start")}
                            </div>
                        </div>
                        <div className="body-item-text"></div>
                    </div>
                </div>
            </div>
        );
    }, [needsPassword, password, error, appGuiSettingState.edition]);

    return dialog;
};
