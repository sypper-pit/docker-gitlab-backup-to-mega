import os
import subprocess
import glob
import re

class BackupManager:
    def __init__(self, backup_dir, cloud_dir, local_limit, cloud_limit):
        self.backup_dir = backup_dir
        self.cloud_dir = cloud_dir
        self.local_limit = local_limit
        self.cloud_limit = cloud_limit

    def extract_timestamp(self, filename):
        # Extract timestamp from filename like '1731206788_2024_11_10_17.5.0-ee_gitlab_backup.tar'
        match = re.search(r'^(\d+)_', os.path.basename(filename))
        return int(match.group(1)) if match else 0

    def get_latest_backups(self):
        backup_files = glob.glob(os.path.join(self.backup_dir, '*_gitlab_backup.tar'))
        return sorted(backup_files, key=self.extract_timestamp, reverse=True)

    def clean_old_backups(self, backups):
        if len(backups) > self.local_limit:
            print(f'Removing old local backups (keeping {self.local_limit})')
            for backup in backups[self.local_limit:]:
                print(f'Removing {os.path.basename(backup)}')
                os.remove(backup)

    def get_cloud_backups(self):
        result = subprocess.run(f'mega-ls {self.cloud_dir}', 
                              shell=True, 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            return sorted(files, key=self.extract_timestamp, reverse=True)
        return []

    def clean_cloud_backups(self):
        cloud_files = self.get_cloud_backups()
        if len(cloud_files) > self.cloud_limit:
            print(f'Removing old cloud backups (keeping {self.cloud_limit})')
            for file in cloud_files[self.cloud_limit:]:
                print(f'Removing from cloud: {file}')
                subprocess.run(f'mega-rm {self.cloud_dir}/{file}', shell=True)

    def create_backup(self):
        print('Creating backup...')
        backup_command = 'docker exec -ti gitlab-web-1 gitlab-backup create'
        result = subprocess.run(backup_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print('Backup created successfully')
        else:
            print('Error creating backup:', result.stderr)

    def upload_to_cloud(self, backup_file):
        print(f'Uploading {os.path.basename(backup_file)} to cloud...')
        mega_command = f'mega-put {backup_file} {self.cloud_dir}'
        result = subprocess.run(mega_command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print('Cloud upload completed successfully')
        else:
            print('Error uploading to cloud:', result.stderr)

    def run(self):
        try:
            self.create_backup()
            latest_backups = self.get_latest_backups()
            
            if not latest_backups:
                print('No backups found')
                return

            self.clean_old_backups(latest_backups)
            self.upload_to_cloud(latest_backups[0])
            self.clean_cloud_backups()
            
            print('Backup process completed successfully')
            
        except Exception as e:
            print(f'Error during backup process: {str(e)}')

# Configuration
BACKUP_CONFIG = {
    'backup_dir': '/var/lib/docker/volumes/gitlab_gitlab-data/_data/backups/',
    'cloud_dir': '/backup/gitlab/',
    'local_limit': 5,
    'cloud_limit': 3
}

if __name__ == "__main__":
    backup_manager = BackupManager(**BACKUP_CONFIG)
    backup_manager.run()
