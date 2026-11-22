class Rightsub < Formula

  desc "Universal Subtitle Mastering & Translation Suite for Movies & TV Series"
  homepage "https://rightsub.ninyo.co"
  url "https://github.com/omerninyo/RightSub/archive/refs/tags/v1.5.1.tar.gz"
  # Recompute after pushing v1.5.1 tag: curl -sL https://github.com/omerninyo/RightSub/archive/refs/tags/v1.5.1.tar.gz | shasum -a 256
  sha256 "7fcb25b0f6484fb5fbfcb4862af1edd6df42bf612bc1179ee6836deb90c52a24"
  version "1.5.1"
  license "MIT"
  head "https://github.com/omerninyo/RightSub.git", branch: "main"

  depends_on "ffmpeg"
  depends_on "python@3.12"

  def install
    libexec.install "rightsub.py", "toolkit.py", "scripts", "site", "README.md", "LICENSE"
    python_bin = Formula["python@3.12"].opt_bin/"python3.12"

    (bin/"rightsub").write <<~SH
      #!/bin/bash
      set -e
      export PYTHONPATH="#{libexec}:${PYTHONPATH:-}"
      exec "#{python_bin}" "#{libexec}/rightsub.py" "$@"
    SH
    chmod 0755, bin/"rightsub"
  end

  def caveats
    <<~EOS
      RightSub is installed! You can now run 'rightsub' from anywhere in your terminal.
      
      Quick Examples:
        rightsub                       # Launch Interactive Mastering Wizard
        rightsub setup                 # First-Time Setup, Hooks & Service Wizard
        rightsub mcp --install         # Connect AI Agents (Antigravity, Claude, Cursor)
        rightsub auto "Movie.mkv"
        rightsub fix-plex "Episode.he.srt"
        rightsub polish "Star Wars.he.srt" --interactive
        rightsub --help
    EOS
  end

  test do
    assert_match "RightSub", shell_output("#{bin}/rightsub --help")
    sample = testpath/"sample.he.srt"
    sample.write "1\n00:00:01,000 --> 00:00:03,000\nשלום עולם?\n"
    system bin/"rightsub", "fix-plex", sample.to_s, "--in-place"
    assert_match "\u200F", sample.read
  end
end
