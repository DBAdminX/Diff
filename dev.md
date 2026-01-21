# dev

## Push

```sh
git tag v1.0.0

git push origin tag v1.0.0
```

## Install

```powershell
winget install DBAdminX.Diff
```

## Update

```powershell
wingetcreate update DBAdminX.Diff -s -u 'https://github.com/DBAdminX/Diff/releases/download/v1.0.2/Diff.exe|x64' -v 'v1.0.2'
```

## Update && Submit

```powershell
wingetcreate update DBAdminX.Diff -u 'https://github.com/DBAdminX/Diff/releases/download/v1.0.2/Diff.exe|x64' -v 'v1.0.2'

winget validate --mainfest .

wingetcreate submit .
```

## Local Install

```powershell
winget settings --enable LocalManifestFiles

winget install --mainfest .
```