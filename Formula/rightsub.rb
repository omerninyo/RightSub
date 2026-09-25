class Rightsub < Formula
  include Language::Python::Virtualenv

  desc "Universal Subtitle Mastering & Translation Suite for Movies & TV Series"
  homepage "https://github.com/omerninyo/RightSub"
  url "https://github.com/omerninyo/RightSub/archive/refs/heads/main.tar.gz"
  version "1.1.0"
  license "MIT"

  depends_on "ffmpeg"
  depends_on "python@3.11"

  def install
    # 1. Create an isolated virtual environment in libexec
    venv = virtualenv_create(libexec, "python3.11")

    # 2. Copy application scripts and assets
    libexec.install Dir["*"]

    # 3. Install required Python packages inside the private virtual environment
    system libexec/"bin/pip", "install", "--upgrade", "pip"
    system libexec/"bin/pip", "install", "-r", libexec/"requirements.txt"

    # 4. Generate the global bin/rightsub launcher script
    (bin/"rightsub").write_env_script(
      libexec/"rightsub.py",
      PATH: "#{libexec}/bin:$PATH"
    )
  end

  def caveats
    <<~EOS
      RightSub is installed! You can now run 'rightsub' from anywhere in your terminal.
      
      Quick Examples:
        rightsub auto "Movie.mkv"
        rightsub fix-plex "Episode.he.srt"
        rightsub --help
    EOS
  end

  test do
    assert_match "RightSub", shell_output("#{bin}/rightsub --help")
  end
end
