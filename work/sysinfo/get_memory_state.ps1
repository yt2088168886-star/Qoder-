$ErrorActionPreference = 'Stop'
$os = Get-CimInstance Win32_OperatingSystem
$out = [ordered]@{
  total_phys_gb   = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
  free_phys_gb    = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
  commit_limit_gb = [math]::Round($os.TotalVirtualMemorySize / 1MB, 2)
  commit_free_gb  = [math]::Round($os.FreeVirtualMemory / 1MB, 2)
  pagefile_usage  = @(Get-CimInstance Win32_PageFileUsage | ForEach-Object {
      [ordered]@{ name = $_.Name; alloc_mb = $_.AllocatedFileSize; used_mb = $_.CurrentUsage }
  })
  pagefile_setting = @(Get-CimInstance Win32_PageFileSetting | ForEach-Object {
      [ordered]@{ name = $_.Name; initial_mb = $_.InitialSize; max_mb = $_.MaximumSize }
  })
  logical_disks = @(Get-CimInstance Win32_LogicalDisk | ForEach-Object {
      [ordered]@{ device = $_.DeviceID; size_gb = [math]::Round($_.Size / 1GB, 1); free_gb = [math]::Round($_.FreeSpace / 1GB, 1) }
  })
  ram_mb = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1MB
  cpu_cores = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum
  cpu_logical = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
}
$out | ConvertTo-Json -Depth 4
