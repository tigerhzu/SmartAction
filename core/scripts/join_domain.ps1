param(
    [Parameter(Mandatory = $true)]
    [string]$Domain,

    [Parameter(Mandatory = $true)]
    [string]$Username,

    [Parameter(Mandatory = $true)]
    [string]$Password
)

try {
    $SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $Credential = New-Object System.Management.Automation.PSCredential("$Domain\$Username", $SecurePassword)

    Add-Computer -DomainName $Domain -Credential $Credential -Force -ErrorAction Stop
    Write-Output "已成功將此電腦加入網域：$Domain"
    exit 0
} catch {
    Write-Error $_.Exception.Message
    exit 1
}
