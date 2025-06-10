{pkgs}: {
  deps = [
    pkgs.rustc
    pkgs.openssl
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
    pkgs.cacert
    pkgs.glib
    pkgs.pkg-config
    pkgs.libffi
    pkgs.libGLU
    pkgs.libGL
    pkgs.zlib
    pkgs.xcodebuild
    pkgs.imagemagickBig
    pkgs.freetype
    pkgs.glibcLocales
  ];
}
