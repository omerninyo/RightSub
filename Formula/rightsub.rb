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
    sha256 cellar: :any_skip_relocation, all: "18a04e9e584d9a506c27667fd5846e668615fe033047a99bd94b7eb5bc405065"
  end

  depends_on "ffmpeg"

  def install
    libexec.install Dir["*"]

    (bin/"rightsub").write <<~SH
      #!/bin/bash
      DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
      export PYTHONPATH="$DIR/libexec:$PYTHONPATH"
      exec python3 "$DIR/libexec/rightsub.py" "$@"
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
