class Rightsub < Formula

  desc "Universal Subtitle Mastering & Translation Suite for Movies & TV Series"
  homepage "https://github.com/omerninyo/RightSub"
  url "https://github.com/omerninyo/RightSub/archive/refs/tags/v1.2.0.tar.gz"
  sha256 "633e4b34e2707975ab9d1684add54c844065ae9187f1365c84342344ea4f16d8"
  version "1.2.0"
  license "MIT"
  head "https://github.com/omerninyo/RightSub.git", branch: "main"

  bottle do
    root_url "https://github.com/omerninyo/homebrew-tap/releases/download/v1.2.0"
    rebuild 2
    sha256 cellar: :any_skip_relocation, all: "0e345f26e67b80e603afaa09ced93bc4ef247c2bd7dfc01f4aefeb53b5f8bb9d"
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
