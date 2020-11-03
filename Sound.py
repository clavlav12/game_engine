from pygame import mixer, init
from enum import Enum
import os
mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
cwd = os.getcwd()


class Sounds(Enum):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    death = mixer.Sound(r"sounds effects\death effect.wav")
    gun_shot = mixer.Sound(r"sounds effects\gun sound.wav")
    gun_shot.set_volume(mixer.music.get_volume() / 15)
    jump = mixer.Sound(r"sounds effects\jump sound.wav")
    jump.set_volume(mixer.music.get_volume() / 6)
    beep = mixer.Sound(r"sounds effects\beep.wav")
    large_beep = mixer.Sound(r'sounds effects\large beep.wav')
    button_push = mixer.Sound(r'sounds effects\button push.wav')
    explosion = mixer.Sound(r'sounds effects\explosion.ogg')
    explosion.set_volume(mixer.music.get_volume() / 15)
    os.chdir(cwd)


class InvalidSoundError(Exception):
    pass


class Player:
    """alternative framework for pygame mixer class"""
    def __init__(self):
        self.mute = False
        self.music = Music()

    def toggle_music(self):
        self.music.toggle()

    def toggle_mute(self):
        self.mute = not self.mute

    def check_music(self):
        """Called from mainloop, makes sure that the music is not playing if mute is on."""
        if self.mute and self.music.playing:  # mute is on but music is not paused
            self.music.pause()
        elif not self.mute and self.music.paused:  # music is not muted but paused
            self.music.unpause()

    def play_sound(self, sound):
        try:
            if not self.mute:
                sound.value.play()
        except AttributeError:
            raise InvalidSoundError('Only use sound of enum class "Sounds"')


class Music:
    """Handel music staff, including toggle music action"""
    def __init__(self):
        self.paused = mixer.music.get_busy()
        self.playing = None
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        mixer.music.load(r"sounds effects\music sound.wav")
        os.chdir(cwd)
        mixer.music.set_volume(mixer.music.get_volume() / 7)
        mixer.music.pause()

    @property
    def playing(self):
        """Opposite of self.paused"""
        return not self.paused

    @playing.setter
    def playing(self, value):
        self.paused = not value

    def play(self):
        self.paused = False
        mixer.music.play(-1)

    def pause(self):
        """Pause the music"""
        self.paused = True
        mixer.music.pause()

    def unpause(self):
        """Unpause the music"""
        self.paused = False
        mixer.music.pause()

    def toggle(self):
        """Toggle music on/off"""
        if self.paused:
            mixer.music.unpause()
        if not self.paused:
            mixer.music.pause()
        self.paused = not self.paused

    def restart(self):
        self.play()
