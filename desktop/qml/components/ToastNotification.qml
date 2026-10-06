import QtQuick 2.15
import QtQuick.Controls 2.15
import ".."
import "."

Item {
    id: root
    width: Math.min(420, Math.max(280, msgText.implicitWidth + 48))
    height: Math.max(48, msgText.height + 24)
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.bottomMargin: 5
    anchors.leftMargin: 20
    z: 9999

    property string message: ""
    property string type: "info" // 'info', 'success', 'warning', 'error'
    property bool showing: false

    function showToast(toastType, toastMsg) {
        type = toastType
        message = toastMsg
        showing = true
        hideTimer.restart()
    }

    Timer {
        id: hideTimer
        interval: 3500
        onTriggered: root.showing = false
    }

    Rectangle {
        id: toastBox
        anchors.fill: parent
        radius: Theme.radiusMd
        color: Theme.surfaceElevated
        border.color: {
            if (root.type === "success") return Theme.success;
            if (root.type === "error") return Theme.error;
            if (root.type === "warning") return Theme.warning;
            return Theme.primaryLight;
        }
        border.width: 1

        opacity: root.showing ? 1.0 : 0.0
        scale: root.showing ? 1.0 : 0.9
        Behavior on opacity { NumberAnimation { duration: 200 } }
        Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutBack } }

        Row {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            FaIcon {
                anchors.verticalCenter: parent.verticalCenter
                icon: {
                    if (root.type === "success") return Icons.checkCircle;
                    if (root.type === "error") return Icons.timesCircle;
                    if (root.type === "warning") return Icons.exclamationTriangle;
                    return Icons.infoCircle;
                }
                size: 16
                iconColor: {
                    if (root.type === "success") return Theme.success;
                    if (root.type === "error") return Theme.error;
                    if (root.type === "warning") return Theme.warning;
                    return Theme.primaryLight;
                }
            }

            Text {
                id: msgText
                text: root.message
                color: Theme.textPrimary
                font.pixelSize: 12
                font.weight: Font.DemiBold
                anchors.verticalCenter: parent.verticalCenter
                width: root.width - 48
                wrapMode: Text.Wrap
            }
        }
    }
}