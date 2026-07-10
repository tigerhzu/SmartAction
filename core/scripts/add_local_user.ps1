param(
    [Parameter(Mandatory = $true)]
    [string]$Username,

    [Parameter(Mandatory = $true)]
    [string]$Password,

    [string]$FullName = "",

    [string]$AddToAdmins = "false"
)

try {
    $existing = Get-LocalUser -Name $Username -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Error "使用者 '$Username' 已存在。"
        exit 1
    }

    $SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    New-LocalUser -Name $Username -Password $SecurePassword -FullName $FullName `
        -PasswordNeverExpires -ErrorAction Stop
    Write-Output "已建立使用者：$Username"

    if ($AddToAdmins -eq "true") {
        Add-LocalGroupMember -Group "Administrators" -Member $Username -ErrorAction Stop
        Write-Output "已加入 Administrators 群組"
    }

    Write-Output "SUCCESS"
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
