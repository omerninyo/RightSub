class Rightsub < Formula

  desc "Universal Subtitle Mastering & Translation Suite for Movies & TV Series"
  homepage "https://github.com/omerninyo/RightSub"
  url "https://github.com/omerninyo/RightSub/archive/refs/tags/v1.3.0.tar.gz"
  sha256 "8979fadd6b742e42ad564c5a00e9649e74c27cfd6d188b80f829a60701144199"
  version "1.3.0"
  license "MIT"
  head "https://github.com/omerninyo/RightSub.git", branch: "main"

  bottle do
    root_url "https://github.com/omerninyo/homebrew-tap/releases/download/v1.3.0"
    rebuild 11
    sha256 cellar: :any_skip_relocation, all: "7326e8147b823ac0809c7541316b30c68a77cdf2ff370e7b3e77dab7169d7930"
  end

  depends_on "ffmpeg"

  def install
    libexec.install Dir["*"]

    (bin/"rightsub").write <<~SH
      #!/bin/bash
      set -e
      TARGET="${BASH_SOURCE[0]}"
      while [ -L "$TARGET" ]; do
        DIR="$(cd -P "$(dirname "$TARGET")" >/dev/null 2>&1 && pwd)"
        TARGET="$(readlink "$TARGET")"
        [[ $TARGET != /* ]] && TARGET="$DIR/$TARGET"
      done
      REAL_PREFIX="$(cd -P "$(dirname "$TARGET")/.." >/dev/null 2>&1 && pwd)"
      export PYTHONPATH="$REAL_PREFIX/libexec:$PYTHONPATH"
      exec python3 "$REAL_PREFIX/libexec/rightsub.py" "$@"
    SH
    chmod 0755, bin/"rightsub"
  end

  def caveats
    <<~EOS
      RightSub is installed! You can now run 'rightsub' from anywhere in your terminal.
      
      Quick Examples:
        rightsub auto "Movie.mkv"
        rightsub fix-plex "Episode.he.srt"
        rightsub polish "Star Wars.he.srt"
        rightsub --help
    EOS
  end

  test do
    assert_match "RightSub", shell_output("#{bin}/rightsub --help")
  end
end
