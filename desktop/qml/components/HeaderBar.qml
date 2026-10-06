import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CGTips 1.0
import ".."
import "."

Rectangle {
    id: root
    height: 60
    implicitHeight: 60
    Layout.preferredHeight: 60
    Layout.minimumHeight: 60
    Layout.fillWidth: true
    Layout.fillHeight: false
    color: Theme.surface
    border.color: Theme.border
    border.width: 1

    property string title: "3D Asset Gallery"
    property string subtitle: "Browse models and assets in storage"
    signal searchRequested(string query)
    signal openLicenseDialog()

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        spacing: 16

        ColumnLayout {
            spacing: 2
            Text {
                text: root.title
                color: Theme.textPrimary
                font.pixelSize: 16
                font.bold: true
            }
            Text {
                text: root.subtitle
                color: Theme.textMuted
                font.pixelSize: 11
            }
        }

        Item {
            Layout.fillWidth: true
        }

        // Quick Search Field (filters local ./data library)
        Rectangle {
            width: 280
            height: 36
            radius: Theme.radiusMd
            color: Theme.surfaceElevated
            border.color: headerSearchInput.activeFocus ? Theme.primary : Theme.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 8

                FaIcon {
                    icon: Icons.search
                    size: 12
                    iconColor: Theme.textMuted
                }

                TextInput {
                    id: headerSearchInput
                    Layout.fillWidth: true
                    color: Theme.textPrimary
                    font.pixelSize: 12
                    selectByMouse: true
                    clip: true

                    Text {
                        text: I18n.t("search_placeholder")
                        color: Theme.textMuted
                        font.pixelSize: 12
                        visible: !headerSearchInput.text && !headerSearchInput.activeFocus
                        anchors.fill: parent
                        verticalAlignment: Text.AlignVCenter
                    }

                    onTextChanged: {
                        root.searchRequested(text.trim())
                    }
                }

                FaIcon {
                    icon: Icons.times
                    size: 11
                    iconColor: Theme.textMuted
                    visible: headerSearchInput.text.length > 0
                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            headerSearchInput.text = ""
                            root.searchRequested("")
                        }
                    }
                }
            }
        }

        // Open ./data Storage Directory
        Rectangle {
            Layout.minimumWidth: storageRow.implicitWidth + 32
            Layout.preferredWidth: storageRow.implicitWidth + 32
            Layout.maximumWidth: 210
            height: 36
            radius: Theme.radiusMd
            color: storageMouse.containsMouse ? Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.2) : Theme.surfaceElevated
            border.color: Qt.rgba(Theme.primary.r, Theme.primary.g, Theme.primary.b, 0.3)

            RowLayout {
                id: storageRow
                anchors.centerIn: parent
                spacing: 6
                FaIcon {
                    icon: Icons.folderOpen
                    size: 12
                    iconColor: Theme.primaryLight
                }
                Text {
                    text: I18n.t("open_storage_btn")
                    color: Theme.primaryLight
                    font.pixelSize: 11
                    font.bold: true
                }
            }

            MouseArea {
                id: storageMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: Bridge.openFolder("")
            }
        }
    }
}
