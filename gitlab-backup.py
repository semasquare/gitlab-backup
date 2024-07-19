#!/usr/bin/env python3

import math
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

import gitlab

SECONDS_PER_MINUTE = 60

def exportProjects():
    # Get All member projects from gitlab
    gl = gitlab.Gitlab(url=GITLAB_URL,
                       private_token=GITLAB_API_TOKEN)

    group = gl.groups.get(GITLAB_GROUP_NAME)
    groupProjects = group.projects.list(iterator=True, include_subgroups=True)
    exports = {}
    for groupProjectIndex, groupProject in enumerate(groupProjects):
        print(f"Starting export of: {groupProject.path_with_namespace}")

        # create export
        project = gl.projects.get(groupProject.id)
        exports[groupProject.path_with_namespace] = project.exports.create()

        if ((groupProjectIndex + 1) % EXPORTS_PER_MINUTE == 0):
            print(
                f"Waiting {SECONDS_PER_MINUTE} seconds to not exceed rate limit")
            time.sleep(SECONDS_PER_MINUTE)
            

    return exports


def downloadExports(backupPath, backupName, exports):
    print("Starting download of backups")
    # download exports
    while (len(exports) > 0):
        for exportIndex, exportName in enumerate(list(exports)):
            export = exports[exportName]
            export.refresh()
            if export.export_status == 'finished':
                dailyBackupPath = Path(backupPath, "daily", backupName)
                if not os.path.exists(dailyBackupPath):
                    os.makedirs(dailyBackupPath)
                exportFileName = f"{backupStart.strftime('%Y-%m-%d')}__{exportName.replace('/', '__')}.tgz"
                fullExportPath = Path(dailyBackupPath, exportFileName)

                print(f"Starting download of: {fullExportPath}")
                downloadStart = datetime.now()
                with open(fullExportPath, 'wb') as f:
                    export.download(streamed=True, action=f.write)
                downloadEnd = datetime.now()

                # remove export
                exports.pop(exportName, None)

                if len(exports) == 0:
                    break

                # start only one download per minute
                downloadDuration = downloadEnd - downloadStart
                print(f"Download finished after {downloadDuration}")
                if (downloadDuration.total_seconds() < SECONDS_PER_MINUTE):
                    print(
                        f"Waiting {SECONDS_PER_MINUTE - downloadDuration.total_seconds()} seconds to not exceed rate limit")
                    time.sleep(SECONDS_PER_MINUTE -
                               downloadDuration.total_seconds())

            time.sleep(1)


def createDailyBackup(backupPath, backupName):
    print(f"Start daily backup {backupName}")
    exportedProjects = exportProjects()

    downloadExports(backupPath, backupName, exportedProjects)


def createMonthlyBackup(backupPath, backupName):
    monthlyBackupPrefix = backupName[:7]
    foundBackupOfCurrentMonth = False
    for root, dirs, files in os.walk(Path(backupPath, "monthly"), topdown=False):
        for dir in dirs:
            if dir.startswith(monthlyBackupPrefix):
                print(f"Found backup for current month: {dir}")
                foundBackupOfCurrentMonth = True
                break

    dailyBackup = Path(backupPath, "daily", backupName)
    monthlyBackup = Path(backupPath, "monthly", backupName)
    if (foundBackupOfCurrentMonth == False):
        shutil.copytree(dailyBackup, monthlyBackup)
        print(f"Backup {dailyBackup} copied to {monthlyBackup}")


def removeOldBackups(backupPath):
    now = datetime.now()
    print(
        f"Start removing backups older than {DAILY_BACKUP_RETENTION_PERIOD} days")
    for root, dirs, files in os.walk(Path(backupPath, "daily"), topdown=False):
        for dir in dirs:
            backupDate = datetime.strptime(dir, "%Y-%m-%d")
            daysSinceBackup = math.trunc((
                now - backupDate).total_seconds() / (24 * 60 * 60))
            if (daysSinceBackup > DAILY_BACKUP_RETENTION_PERIOD):
                shutil.rmtree(Path(backupPath, "daily", dir))
                print(f"Backup removed: {dir}")

    print("Removing backups finished")


if __name__ == '__main__':
    load_dotenv()
    GITLAB_API_TOKEN = os.getenv('GITLAB_API_TOKEN')
    GITLAB_GROUP_NAME = os.getenv('GITLAB_GROUP_NAME')
    GITLAB_URL = os.getenv('GITLAB_URL', 'https://gitlab.com')
    DAILY_BACKUP_RETENTION_PERIOD = os.getenv(
        'DAILY_BACKUP_RETENTION_PERIOD', 5)
    BACKUP_PATH= os.getenv('BACKUP_PATH', './backups')

    # https://docs.gitlab.com/ee/user/project/settings/import_export.html#rate-limits
    EXPORTS_PER_MINUTE = os.getenv('EXPORTS_PER_MINUTE', 6)

    print("Backup started")
    backupStart = datetime.now()
    backupName = f"{backupStart.strftime('%Y-%m-%d')}"

    createDailyBackup(BACKUP_PATH, backupName)
    createMonthlyBackup(BACKUP_PATH, backupName)
    removeOldBackups(BACKUP_PATH)

    backupEnd = datetime.now()
    print(f"Backup finished after {backupEnd - backupStart}")
