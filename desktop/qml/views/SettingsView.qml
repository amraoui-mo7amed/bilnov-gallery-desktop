import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "../components"

Flickable {
    id: root
    contentWidth: width
    contentHeight: contentCol.implicitHeight + 40
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: ScrollBar {
        policy: ScrollBar.AsNeeded
    }

    property string clientStatusText: ""

    Connections {
        target: Bridge
        function onClientStatusResult(success, statusCode, msg, licenseKey) {
            root.clientStatusText = I18n.tMsg(statusCode) + " — " + I18n.tMsg(msg);
            if (licenseKey.length > 0 && licKeyInput.text.length === 0) {
                licKeyInput.text = licenseKey;
            }
        }
        function onClientProfileResult(success, msg) {
            root.clientStatusText = I18n.tMsg(msg);
        }
    }

    ColumnLayout {
        id: contentCol
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 24
        spacing: 24

        // ---------------------------------------------------------
        // Header Section
        // ---------------------------------------------------------
        ColumnLayout {
            spacing: 4
            Text {
                text: I18n.t("settings_title")
                color: Theme.textPrimary
                font.pixelSize: 20
                font.bold: true
            }
            Text {
                text: I18n.t("settings_subtitle")
                color: Theme.textMuted
                font.pixelSize: 12
            }
        }

        // ---------------------------------------------------------
        // Card 1: Interface Language (EN / FR only)
        // ---------------------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: langCol.implicitHeight + 32

            ColumnLayout {
                id: langCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    spacing: 10
                    FaIcon {
                        icon: Icons.globe
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: I18n.t("section_language_title")
                            color: Theme.textPrimary
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: I18n.t("section_language_desc")
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                    }
                }

                RowLayout {
                    spacing: 12
                    Layout.topMargin: 4

                    // English Button
                    Rectangle {
                        Layout.minimumWidth: langEnRow.implicitWidth + 32
                        Layout.preferredWidth: langEnRow.implicitWidth + 32
                        Layout.maximumWidth: 210
                        height: 42
                        radius: Theme.radiusMd
                        color: I18n.currentLanguage === "en" ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated
                        border.color: I18n.currentLanguage === "en" ? Theme.primary : Theme.border
                        border.width: 1

                        RowLayout {
                            id: langEnRow
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon {
                                icon: Icons.check
                                size: 12
                                iconColor: Theme.primaryLight
                                visible: I18n.currentLanguage === "en"
                            }
                            Text {
                                text: "English (EN)"
                                color: I18n.currentLanguage === "en" ? "white" : Theme.textSecondary
                                font.pixelSize: 12
                                font.bold: I18n.currentLanguage === "en"
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: I18n.setLanguage("en")
                        }
                    }

                    // Français Button
                    Rectangle {
                        Layout.minimumWidth: langFrRow.implicitWidth + 32
                        Layout.preferredWidth: langFrRow.implicitWidth + 32
                        Layout.maximumWidth: 210
                        height: 42
                        radius: Theme.radiusMd
                        color: I18n.currentLanguage === "fr" ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated
                        border.color: I18n.currentLanguage === "fr" ? Theme.primary : Theme.border
                        border.width: 1

                        RowLayout {
                            id: langFrRow
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon {
                                icon: Icons.check
                                size: 12
                                iconColor: Theme.primaryLight
                                visible: I18n.currentLanguage === "fr"
                            }
                            Text {
                                text: "Français (FR)"
                                color: I18n.currentLanguage === "fr" ? "white" : Theme.textSecondary
                                font.pixelSize: 12
                                font.bold: I18n.currentLanguage === "fr"
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: I18n.setLanguage("fr")
                        }
                    }
                }
            }
        }

        // ---------------------------------------------------------
        // Card 2: Trial / License Expiry Countdown
        // ---------------------------------------------------------
        Rectangle {
            id: card2
            property bool licenseMode: Bridge.isLicensed && Bridge.licenseStatusCode !== "TRIAL"

            Layout.fillWidth: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: trialCol.implicitHeight + 32

            ColumnLayout {
                id: trialCol
                anchors.fill: parent
                anchors.margins: 16
                spacing: 14

                RowLayout {
                    spacing: 10
                    FaIcon {
                        icon: Icons.clock
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: card2.licenseMode ? I18n.t("section_license_title") : I18n.t("section_trial_title")
                            color: Theme.textPrimary
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: card2.licenseMode ? I18n.t("section_license_desc") : I18n.t("section_trial_desc")
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                    }

                    Item { Layout.fillWidth: true }

                    // Refresh Network Time Button
                    Rectangle {
                        height: 32
                        Layout.minimumWidth: refreshRow.implicitWidth + 32
                        Layout.preferredWidth: refreshRow.implicitWidth + 32
                        Layout.maximumWidth: 210
                        radius: Theme.radiusMd
                        color: refreshMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.25) : Theme.surfaceElevated
                        border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.4)

                        RowLayout {
                            id: refreshRow
                            anchors.centerIn: parent
                            spacing: 6
                            FaIcon {
                                icon: Icons.sync
                                size: 11
                                iconColor: Theme.primaryLight
                            }
                            Text {
                                text: card2.licenseMode ? I18n.t("license_refresh_btn") : I18n.t("trial_refresh_btn")
                                color: Theme.primaryLight
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }

                        MouseArea {
                            id: refreshMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: card2.licenseMode ? Bridge.verifyLicense() : Bridge.refreshTrialStatus()
                        }
                    }
                }

                // Countdown Pill & Details Display
                RowLayout {
                    spacing: 16
                    Layout.fillWidth: true

                    // Big Countdown Box
                    Rectangle {
                        width: 260
                        height: 70
                        radius: Theme.radiusMd
                        color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.15)
                        border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.4)

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 2
                            RowLayout {
                                spacing: 8
                                Text {
                                    text: card2.licenseMode
                                          ? Bridge.licenseCountdownText
                                          : Bridge.trialDaysRemaining + " " + I18n.t("days_left") + ", " + Bridge.trialHoursRemaining + "h"
                                    color: Theme.primaryLight
                                    font.pixelSize: 17
                                    font.bold: true
                                }
                            }
                            Text {
                                text: card2.licenseMode
                                      ? (Bridge.licenseIsPerpetual ? I18n.t("license_perpetual_suffix") : I18n.t("license_remaining_suffix"))
                                      : I18n.t("trial_remaining_suffix")
                                color: Theme.textMuted
                                font.pixelSize: 10
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }

                    // Metadata details column
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        RowLayout {
                            spacing: 6
                            Rectangle {
                                width: 8
                                height: 8
                                radius: 4
                                color: (!card2.licenseMode && Bridge.isNetworkTimeSynced) || (card2.licenseMode && Bridge.isLicensed)
                                       ? Theme.success
                                       : (card2.licenseMode ? Theme.error : Theme.warning)
                            }
                            Text {
                                text: card2.licenseMode
                                      ? (Bridge.licenseMessage || I18n.t("field_license_status"))
                                      : (Bridge.isNetworkTimeSynced ? I18n.t("trial_net_verified") : I18n.t("trial_local_verified"))
                                color: (!card2.licenseMode && Bridge.isNetworkTimeSynced) || (card2.licenseMode && Bridge.isLicensed)
                                       ? Theme.success
                                       : (card2.licenseMode ? Theme.error : Theme.warning)
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }

                        Text {
                            text: card2.licenseMode
                                  ? I18n.t("license_expires_on") + (Bridge.licenseExpiresAt || "Perpetual")
                                  : I18n.t("trial_expires_on") + Bridge.trialExpiresAt
                            color: Theme.textSecondary
                            font.pixelSize: 11
                        }
                    }
                }
            }
        }

        // ---------------------------------------------------------
        // Card 3: Activate or Change License
        // ---------------------------------------------------------
        Rectangle {
            Layout.fillWidth: true
            radius: Theme.radiusMd
            color: Theme.surface
            border.color: Theme.border
            border.width: 1
            implicitHeight: activateCol.implicitHeight + 32

            ColumnLayout {
                id: activateCol
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    spacing: 10
                    FaIcon {
                        icon: Icons.key
                        size: 15
                        iconColor: Theme.primaryLight
                    }
                    ColumnLayout {
                        spacing: 2
                        Text {
                            text: I18n.t("activate_section_title")
                            color: Theme.textPrimary
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: I18n.t("activate_section_desc")
                            color: Theme.textMuted
                            font.pixelSize: 11
                        }
                    }
                }

                // Section: Request a key
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Layout.topMargin: 4

                    Text {
                        text: I18n.t("section_details_title")
                        color: Theme.textSecondary
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Text {
                        text: I18n.t("section_details_desc")
                        color: Theme.textMuted
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                }

                // Full Name & Email Inputs Grid
                GridLayout {
                    columns: contentCol.width >= 600 ? 2 : 1
                    columnSpacing: 14
                    rowSpacing: 10
                    Layout.fillWidth: true

                    // Full Name Input
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("customer_name_label")
                            color: Theme.textSecondary
                            font.pixelSize: 11
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            height: 36
                            radius: 6
                            color: Theme.surfaceElevated
                            border.color: nameInput.activeFocus ? Theme.primary : Theme.border
                            TextInput {
                                id: nameInput
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                verticalAlignment: Text.AlignVCenter
                                color: Theme.textPrimary
                                font.pixelSize: 12
                                selectByMouse: true
                                Text {
                                    text: I18n.t("customer_name_placeholder")
                                    color: Theme.textMuted
                                    font.pixelSize: 12
                                    visible: !nameInput.text && !nameInput.activeFocus
                                    anchors.fill: parent
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }

                    // Email Input
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: I18n.t("email_label")
                            color: Theme.textSecondary
                            font.pixelSize: 11
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            height: 36
                            radius: 6
                            color: Theme.surfaceElevated
                            border.color: emailInput.activeFocus ? Theme.primary : Theme.border
                            TextInput {
                                id: emailInput
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                verticalAlignment: Text.AlignVCenter
                                color: Theme.textPrimary
                                font.pixelSize: 12
                                selectByMouse: true
                                Text {
                                    text: I18n.t("email_placeholder")
                                    color: Theme.textMuted
                                    font.pixelSize: 12
                                    visible: !emailInput.text && !emailInput.activeFocus
                                    anchors.fill: parent
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }
                }

                // Request Key / Check Status Buttons
                RowLayout {
                    Layout.topMargin: 4
                    spacing: 8

                    Rectangle {
                        Layout.minimumWidth: registerBtnRow.implicitWidth + 32
                        Layout.preferredWidth: registerBtnRow.implicitWidth + 32
                        Layout.maximumWidth: 210
                        height: 40
                        radius: 8
                        color: registerMouse.containsMouse ? Theme.primaryHover : Theme.primary

                        RowLayout {
                            id: registerBtnRow
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon {
                                icon: Icons.plus
                                size: 12
                                iconColor: "white"
                            }
                            Text {
                                text: I18n.t("register_btn")
                                color: "white"
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }

                        MouseArea {
                            id: registerMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                var name = nameInput.text.trim();
                                var email = emailInput.text.trim();

                                if (name.length < 2) {
                                    Bridge.toast("error", I18n.t("val_name_err"));
                                    return;
                                }
                                if (email.length < 5 || email.indexOf("@") === -1) {
                                    Bridge.toast("error", I18n.t("val_email_err"));
                                    return;
                                }

                                root.clientStatusText = "";
                                Bridge.registerClientProfile(name, email, "", "");
                            }
                        }
                    }

                    Rectangle {
                        Layout.minimumWidth: statusBtnRow.implicitWidth + 32
                        Layout.preferredWidth: statusBtnRow.implicitWidth + 32
                        Layout.maximumWidth: 210
                        height: 40
                        radius: 8
                        color: statusMouse.containsMouse ? Theme.surfaceElevated : Theme.surface
                        border.color: Theme.border

                        RowLayout {
                            id: statusBtnRow
                            anchors.centerIn: parent
                            spacing: 8
                            FaIcon {
                                icon: Icons.sync
                                size: 12
                                iconColor: Theme.textMuted
                            }
                            Text {
                                text: I18n.t("check_status_btn")
                                color: Theme.textPrimary
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }

                        MouseArea {
                            id: statusMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                var query = emailInput.text.trim() || Bridge.deviceId;
                                root.clientStatusText = "";
                                Bridge.checkClientStatus(query);
                            }
                        }
                    }
                }

                // -------------------------------------------------
                // Already have a key: key input + Activate button
                // -------------------------------------------------
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: haveKeyCol.implicitHeight + 28
                    radius: 8
                    color: Theme.surfaceElevated
                    border.color: Theme.border
                    Layout.topMargin: 8

                    ColumnLayout {
                        id: haveKeyCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8

                        Text {
                            text: I18n.t("section_have_key_title")
                            color: Theme.textPrimary
                            font.pixelSize: 12
                            font.bold: true
                        }
                        Text {
                            text: I18n.t("section_have_key_desc")
                            color: Theme.textMuted
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        // License Key Input
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text {
                                text: I18n.t("license_key_label")
                                color: Theme.textSecondary
                                font.pixelSize: 11
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                height: 36
                                radius: 6
                                color: Theme.surface
                                border.color: licKeyInput.activeFocus ? Theme.primary : Theme.border
                                TextInput {
                                    id: licKeyInput
                                    anchors.fill: parent
                                    anchors.leftMargin: 10
                                    anchors.rightMargin: 10
                                    verticalAlignment: Text.AlignVCenter
                                    color: Theme.textPrimary
                                    font.pixelSize: 12
                                    font.family: "Monospace"
                                    selectByMouse: true
                                    Text {
                                        text: I18n.t("license_key_placeholder")
                                        color: Theme.textMuted
                                        font.pixelSize: 12
                                        font.family: "Monospace"
                                        visible: !licKeyInput.text && !licKeyInput.activeFocus
                                        anchors.fill: parent
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }

                        // Activate Workstation Button
                        RowLayout {
                            Layout.topMargin: 6
                            spacing: 8

                            Rectangle {
                                Layout.minimumWidth: activateBtnRow.implicitWidth + 32
                                Layout.preferredWidth: activateBtnRow.implicitWidth + 32
                                Layout.maximumWidth: 210
                                height: 40
                                radius: 8
                                color: activateMouse.containsMouse ? Theme.primaryHover : Theme.primary

                                RowLayout {
                                    id: activateBtnRow
                                    anchors.centerIn: parent
                                    spacing: 8
                                    FaIcon {
                                        icon: Icons.key
                                        size: 12
                                        iconColor: "white"
                                    }
                                    Text {
                                        text: I18n.t("activate_btn")
                                        color: "white"
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                }

                                MouseArea {
                                    id: activateMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        var key = licKeyInput.text.trim();
                                        var name = nameInput.text.trim();
                                        var email = emailInput.text.trim();

                                        if (key.length < 10) {
                                            Bridge.toast("error", I18n.t("val_key_err"));
                                            return;
                                        }

                                        if (name.length > 0 || email.length > 0) {
                                            if (name.length < 2) {
                                                Bridge.toast("error", I18n.t("val_name_err"));
                                                return;
                                            }
                                            if (email.length < 5 || email.indexOf("@") === -1) {
                                                Bridge.toast("error", I18n.t("val_email_err"));
                                                return;
                                            }
                                        }

                                        Bridge.activateLicense(key, name, email, "", "");
                                    }
                                }
                            }
                        }
                    }
                }

                Text {
                    visible: root.clientStatusText.length > 0
                    text: root.clientStatusText
                    color: Theme.textMuted
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}
