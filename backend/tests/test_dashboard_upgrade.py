FAKE_APK = b"PK\x03\x04" + b"\x00" * 64


def upload(client, headers, content=FAKE_APK, filename="dashboard.apk"):
    return client.post(
        "/api/admin/dashboard-upgrade",
        headers=headers,
        files={"file": (filename, content, "application/vnd.android.package-archive")},
    )


def test_rejects_files_that_are_not_apks(client, admin_headers):
    assert upload(client, admin_headers, filename="dashboard.zip").status_code == 400
    assert upload(client, admin_headers, content=b"not a zip").status_code == 400


def test_upload_bumps_version_and_serves_the_apk(client, admin_headers, make_user):
    _, headers = make_user()
    before = client.get("/api/app/dashboard-upgrade", headers=headers).json()["version"]

    response = upload(client, admin_headers)
    assert response.status_code == 200, response.text
    assert response.json()["version"] == before + 1

    info = client.get("/api/app/dashboard-upgrade", headers=headers).json()
    assert info["version"] == before + 1
    assert info["uploaded_at"]

    download = client.get("/api/app/dashboard-upgrade/download", headers=headers)
    assert download.status_code == 200
    assert download.content == FAKE_APK
    assert download.headers["content-type"] == "application/vnd.android.package-archive"


def test_download_requires_login(client):
    assert client.get("/api/app/dashboard-upgrade/download").status_code == 401
