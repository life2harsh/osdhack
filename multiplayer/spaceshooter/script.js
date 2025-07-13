     const speedUpSprite = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABdElEQVRYR82W0RXCIAxF0zXcpG7jnyP55xwuYDdxjXpSm/oIoQlHetA/BJLLy4N0IPxN5zkZlwbjc7CmbhOF9l9H2vZ/A3HyQuAsmbGWk2PgvYPg2g9ATXKJDHtqkst22TOYyaUUoogeA8SNnmSdXMohc3rMIfi/FACViEBM5xkBvKTWfA7AaKWTG1BagQgEqpKXwDu5UskqgQeBPmjqATRjBCL3ADp8rxQFE7YB6FqCSHKlTFsTdr+GP3oAn9+4Cbs/xcbb7nbE5s1IS+8RHNKOuSleYv18vH/7efI5cQrufxnfA5y8FFgLYq2dTjSPEHhPRFy7fA/UJN+qBcA1ybf9K/CAyaUEokRo/CDCkzPM8latalhjnEsARI0lwFpnCyKZUwBLDAcCVcgAIhBYBgIALEUEgtdkJYjKv4EqAE9+Pf9fHgiZTvujpQlrbsQhJUjMtXMTDjNh5AZkKrW8hl080P0ptt52rxs3b0bafB5Ay3b8BvT6cqvw5EPXAAAAAElFTkSuQmCC';
        const powerUpSprite = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAABwCAYAAAAXB/A7AAACGklEQVRYR+1ZsXHDMAwk1/AY6egVMkHKdBkpXcpM4BWiLmNkDeVAkcoLhEjAlKy7nFxZJv75AB+QbXmHr+E6Lq7XLsKXz0vzG0dgWKgSQexEYAFn5oTxC3AtBUndcB2XBKoCQJBIYFGxj4JcVMURUv3+XQ0sJ5BqtUENuq3MvK0yY9FMSKJhENvZOfc+ONU8eAuunAcExoWaEIyNTBZwJs4YvwaW0uEKKWaVQFPLJkFLRZOgpUJFUFOhImgdZ7WIx9agtXs2YL8Puq3Mvd06e77h3925t53jZHvVzYPwIcwDAuNCLRWMjSlYwPP0Sxt6DRhTQ5X0uYpgLR0TgaTCRCCpMBNwFWYCrsJEcGwN9vVBt5W5tzXzoGgmJNEQiO0cU7ko58GPNA8ubgywUJ0HEDvNAwN4TjdhvBac00OV9JmaQOxGKwFX8XgFeNRUi8crOLYG+/mg28rc25p2Rvsvvh90tXNMxX2qfi8E91L+XiAwLlTnAcRO88AAnmuWMN4C5rF0bSIo7o33EKCKYxRg0Y9RcGwN9vFBt5W5t1XzgDcTkmgIxHaOwKdBNQ/cdxD+TyQwLFSVQOzEZAFn5oTxd4GB5CQYxrMGm9Sg28rM25p2Rvsvvh/0tXOcbTfdPAjP0vOF2+hgoZoKbZRi0/MFA3iefxPGR9nanYv7+43+Wz8Jzhps4YPcRFY3JgPCwzqDI4tmwgbRTBRQ+wsmv4hBGUclzwAAAABJRU5ErkJggg==';
        const bulletSprite = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAICAYAAADwdn+XAAAAQ0lEQVQoU2NkSPr/n4FUMI+REaYFzgALfPn//z83AwPjVwYGYmlUA6DG/v9PvKswDCBFM8g+6hsAMpUUV1AhECmMRgChtzPdurGgmgAAAABJRU5ErkJggg==';
        const burnSprite = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAABACAYAAAB7jnWuAAAAw0lEQVRoQ+2ZwQ3AIAwDYY7uP1rnoAIJBFXfPkt1F8A4l5CktcBfhc8vPgLu0tpVqlxQ7QfPMCAC+uFTBCJgd6CLUYsYMSdFhIHDAQsG5BCSAHbHvbLgnwy8C1EgVHOQQuTlgDoDRiW0asmI3jAMeDAw3wMkCzIbxoE4EAfiwO4AsSlZSylsSYXviGYICPs/p2P1k3wwoJ6KPPYDFgzsIjAGqL4wEPo5gEFoUYrVt1+VkErBQwD1LMv/kr170AiIA3HgARYMhEG2cflOAAAAAElFTkSuQmCC';
        const popCornSprite = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAGACAYAAADMEWCuAAAIU0lEQVR4Xu1dO5LcNhAlAwdKFchXcOJAiS+gO/guOoHvodB30AWcbOBEZ1Dg1ImrxgXUNAdsAuzXHw45dm+0tcshHhpAo/vhoWeeTv6Zefu32+2GYprnefN59LP0XB8A+N55mmIBlN5/Ahr/eocfD2Cabp9AGxYQoQBu01TH/qUA/PDLb6C9Ho+9//J5+v7TY+4sk4gsgFqhDMGP7z5CAL7//TacrPUfbeNWAHuN7KEMAWBtvADrAkCs0A6BCwA3P5lLWg0tgL9+/nV6/+fv9aP893/++LzrrGYPgOIHPrz7WJdvscLo99050AMg9b68kDui0jgNRfu7tEyGFpCGQrMM6V29ubIBgPSeLFD8QBlz5KfMkTo/uCPyzAFyRAgImqTcCq5J2AKgHpI1lh5Tz1ELaIcAMX/7jGgBDQBahnuOqF2aPbCrIUAbb5fhaMlJDa9CMm0ssAcAbXgDQNP7HgBtw6EAyBVrJ+SyG1JM0LMCBaD8f+SKrT1fWQABwLfodi/Q+H5upVVItmeBwwHsWaE3tuEW8AKY3t5W0S46IbepGZichCcmhHi0O3bdaHRuiJot8jl3dusFc1F+oO3WTroemh3XZdhhR3p8wXH8AAOwR1aEL0O09zQ6VgAfvk23fnqu6D3FA1Z+oG7fd47gsRkRgHmGWBJNYtLGjF0LLOa/z3gkOuIArBly8gOhmVGZXBuugOWCm4jIkxsmP4DSdGT2yqJwR2Sh6MgRWfmBlSPyzAELP8Bjx9BV0BIVe/zArgUQL9gOgToiYtGziyNKfqBnAW2yumxG6NjzgIQSU23Dq+y4LEUPgDqrd84E9iYqnB0nP3B5fiAkPddMRk5QFACti0U9ZBg/wLdZFwDFh93ZtfsFKNjRc9cDAOsH5jn28HrhiFABwxEA4N4XtP85AKreH2EBCwArPwARFOL6nudA/QA68xl71mZGroBEbf77HCAA1sbra0b0nGYIXABMvWcW8OkHLOPfLEO/fsAJgIbKrh9wALDwA1uKxgkAObovjaZ+ALYAmqJpqNp23FM/sFkF1RUrtYRE0SQ/wKlacQPrPJD8AGyBy/MD1qBklRt6+YE22kUnZBg/gDbYdUTtH1M/YDWl9XPdOYC+LPz4vt2YEBDhANBleJx+ACCtv9INkGiCYi8mWBplyallCMb6ARaUdBtlAKz8QHnNVj9wB1DbQC7aGPmBvn5A2zhLTmuPPAcWi/tFek7D0FjA2viDHygW0DTOLOACUHuvbVzBD3AteWhyGqMfcGTHrR94GX5gqx9wWCBGP+AEUCYVQlLQ/YKtfiAIgOZ+wcoVR9B0SOywPNPVDxj9QJx+4AAA6Gn6Q0umBXEPSLiuHG142VIoDizckBgDdAKSUP2AFYB7OzZZoRmCUADlZZAlmqD0kPsFIohoAO0w0FzbBcEAHKofkMLyuvRSP6DaEB4PX+/43tgR88eSHzDRdKfyA4uTyvoD0zRZ+YGsP7AKrGgXbP+IHN2FXf/vASh/k0CEAYiSdmf9ATs/0DJknT1tNBcsZ8dZf6CXP5xyv2Dlir1XPLSh0AX1A4WiUdwx4/FATP2BOwjJ/bbmbi+/r27TNYVRkOFZtGRIKag9AFpiYk1QgLWoRgBi0vMBiOfVHxAA8C06/Pb9qCQYWeBwADUwUcyFcAt4AYQQFBoQ1nvH3DfYL79Hn5wiXuuIZ65HUJwu4TgVwEvoB16eH4D1A9KSK47Iyg/U7XtTf6BJUJDISJOYyPUHWHZkAWA9Qc/6A6GZUZlcWX+gWEFzhvT0+oRZfyDrD4gWQNxwmemj7JhvYlLSmvUJs/4ArK7P+gPP4QcAWW8vLKfje7e8H01MWkdE22/qB6Q8YvT/66Xn1p5YP5f6gdQPrDYj7m73JlY4T6i99OjhB1I/0A5t8gOH8wP5/QXSJvV0fmBzYOE9vEak/aVR+PY9IZSSVP4lGpKp8/sLyEIX1A8oSWqemMToB7L+gCIn7A1BPYDwXPerR7YDEM/TDwgADk/PJQscDmBvGHpu9hj9gGIy9uoTugkKjRXC8wIy86lnx9KWesT/r0dQnD4EpwJAabq8X8CJSs3qSP2AXH8AUNbTEMTVJ3QKGKzRUOlIl6BAyKqXuV8g1x8YqOuR3DCm/kAHgNR4zw+8zP2C1A+Ip+dWgsJef8DghHqeEN6Q8vsLmKlWrhhZ/xJBISkmNjSdJhlpP8wlHNqG6V0hAobkBzTase4cQBiSy/MDIfJ+NDHh23HWH4D3gc6D10vPPb2xfDb1A6kfSP3AxgJIYqoNSvey55Dje3dAYjk9DUvPKRbgXkwKUMMAZP2BngUk8780P7AJSi0roPUDqR8o1qCbNej3G2b9gXYi5v2CkPS8fn+psvBB8gMrC1wiPU/9gJYtS/1AsZilcPqQpLKk1hGfuR5Bcerx/ShHGJk6fA6gNF3qB3p5AboiUj+Q+oGuK7YkqC/DD6R+QPIPT79fkPqB1A+IFkAYsnY3lE5NpaQ1+YHkB7L+AGyB1A/wbbXHD9Szo3u1LWkb3nBE9AdNdrT6PqNv003b+D3FX2M9PTlFTRf1XPID1xIwaFbAISQVCsCTng9ZMsv1/1CKxgLAWp8w6w+sDq161BwSGYel5yNuUAIRBiD1AxZ6pueIXuZ+wcYTpn4gchWkfqAXJyY/IEXPyQ/A2XHWJ7w8P2C9dWkSNvPtOKxAIoVnUjh2SGLSEhSS82jYDXd27X4BCnb03PUAnE7RnAoATc9TP+DxA6kfSP1Al6SyJKgvww+kfkDaLVM/EFYkUzI11ScUT8/pRVJcyAskZv2B0RAkPyBNzuQHkh+ALXB5fiDrD/BoV1r/TYr/P9cP/AtYaT8mrQ1H+AAAAABJRU5ErkJggg==';
        const shipSprite = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAFACAYAAADd+X4aAAAGsUlEQVR4Xu1dsY4cRRCdizgHRASWzj5ZugAROSODDAJ/AjHS/YOFLBZZiMwfcIiYTyCADL6AyHJgCR0+yQERgU20qPau5nq6q2fqdVfPtOWa5G53e7pev+qemXpTU3M0bLwdbWx/mADYvd7vd3ePxu/izy3AJgDICIMgAIfPF8MwPLkFZglEBDCCeHoNYLIZA8kCGEeeG64RkGQSHvxOlGu3SiDyKpCoXwJUCGQKoMRw5RyxB0CAADYmAF4N+/29p0tcT38/+f50/OLq7d/wgW3cgYxTTygAFdwZRqoZUAHgRgKQhIFmLIRIAyAJA58enw5X31zeNj+7+fclNFZd4ydH6fH95Pj+ePg9AGAAN12efH06XP10OfBf+pr+n9vmJmcya0MA/3z88/D28t9J3/fenA+v7lwM/PfgsjfnNgBoJZALyDBvDOD49EMdrUCr//78/NYFvAxp/7OHfwDd4E3JMO+VTMKWxkPDCQBmoAUAybAZAx+9+MrmUEy9fPDw9/QKCHfxMDfiuLvJHLAAgBgnMOLZqwQIalicAyVuKDUsAkBGXmt4EQAZkABZGZ4FwEZCANaGswBCQwSgleHsJCxY9lW7wBeRVdaEnR3Au6EPkOtC4cJyHszqAyxQhAatgczqA3MjtQIi6gMIxbVAxGUoUT9xgyRgABFx2NeiCyC1hHoGgeQnISLTxD4DQFSH5yb6QBiUbKYPNBUo2EU5fSBkgNo2YSGcJ5I+wCA21Qc4Omawq+sDMYBV9YHQBavrA/EkbBEhh3NQ1AdahudsPKsPtFZHVPpAKQOuD8QnQjSScn2gWKJBqc5dZ2YBuD7AepEV1SoXIPGAVVsPz/tioNv8AdcHpCVXG5ZndcKl0DwGUwukSB+wZGRRH0CPeCgj5gDQFZPctvvxNTbmiwfG+QMoAA3cObdUM6ABwG0kIGL+QAsWcmKnmD9w/tdt/sDut+tdd18gY9W1JUZmb98TEAbAXXr+gI5cXSvPHyCekmXYQh1R6QOEhjQCFIDrA64P1MaOrg+IDHj+gO5UYtOqr+jYZkxYL50xQJnV4Z2t+DM2OFXrKQOc2s0gwlRv4G6oyvJNIxkA/UgG136+QDSYG44RI+kkRDPsK4HIqwAFwS5DnL84Bwo6O+wCMpKfhKUAQBCeP1DNAOQpbf6AVh/QJrjsotz3UKhIGKD8gc30gfj2/er6gOcP8IxGA1RoJQzDJPd8lfCcAXr+gOSq4thwzu9IwGoOADE+0YjCESFZ9nMTTLM6kisi1Dg64hhUsQtqDTMQzx9IGPDnCzRLx7JNZ+G55dCUfaWBiesDTJ3rA8pJhEbDsyej8UfXB7T0G+hHyb1jNLHd5PkCGkjT9H6vPxDPlaX6A5vpAwQ0fPx/dX0gBrDq8wW8Erz+QEtxwusPuD6wyAA3QEN02q80WnZ9wPUB1wc8PO+MAc8fiBMWPH9AE6SCd8tdH5hnoEQZkdwEuKX67rmJPuD1B7qrP6DRB7TJC9Ic5YSG5PmC7uoPUAGE/bNfJoNoVp8wrD8QuuDbT64BfPf8UfbA/MOXunKCj3/9bNLH6AKvP+D1B2qiYmlmIpFy8c3r3JJAjFMf4mW56wOaS0GU6lyfrg+4PtBZdKyZ/sZtOmPA9QHXB2iGowEqEIiq5XoYBPVcCMQ+vR8EYg8AZMPzB6oZgE4N/v4CIZEhORt29f4CCtM5PGfwzfSBMH8A1QegiRg0nkg0YYSsfcilxjDvmyzDlsZVZUBaAGhaCMWsFAz5BK1FlJsDSEWeyRywAIAYz+oDJUBQw+IqKHFDqWERADLyWsOLAMjAZmXD4xerHVwTvPGt9Ai4eFW8eWk4y5Fp++osOtbCNmzXGQOuD7g+4PoAqo5Ix4N3Vh8oTe/3/AHotKCtP4A+5gGBiDQksf7AZu837C5/YNXnC/z9BaXV+5EV4PUHFgOTkrvmUqfIfWWT/IEwOwYN4cTLcgrR5lJz4nScmtgxAYCE6DWGF8PzpeWFUp3rL6sRuT7AepEV1SoXLPm9xe+dRccthrjQZ2cMuD7g+oDrA++1PkDup0tzNDA10QfYOP1FAaiO3l5/IKZpqf7AZvoAAe0qf2BVfYBXgtcf8PoDKAP+/oL4IIeIE7SvP19QLNGgVKuC01Ck8vcbEmXEiBXVKheoLq+MG3UWHRuPTtNdZwy4PuD6gOsD77U+4PkDpQxojvdjG88fEISKJLecomPeDkLF2XSvpu839PcXMNlogAqtBH9/QURXksaD0u/6gOsDtbGj6wMiA/5+Q/TYXtN+8+j4f1oo2JvjbO9WAAAAAElFTkSuQmCC';
        const explosionSprite = 'data:image/png;base64,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';

        var TOP_TURN = false;
        var canvas = document.getElementById('viewport');
        var context = canvas.getContext('2d');
        var fps = 1000 / 60;
        var then = Date.now();
        var startTime = then;
        var WAVE = 1800;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        context.imageSmoothingEnabled = false;

        var UP = 38, DOWN = 40, LEFT = 37, RIGHT = 39, SHOOT = 32, RESET = 82, START = 13, MULTIPLAYER = 77, REVIVE = 82, ESCAPE = 27;

        var gameState = {
            isMultiplayer: false,
            socket: null,
            connected: false,
            playerId: null,
            roomId: null
        };

        function State(name, updater, renderer) {
            this.name = name;
            this.updater = updater;
            this.renderer = renderer;
        }

        function Intersection() {}

        Intersection.rectanglesIntersect = function(rect1, rect2) {
            return (
                rect1.x < rect2.x + rect2.width &&
                rect1.x + rect1.width > rect2.x &&
                rect1.y < rect2.y + rect2.height &&
                rect1.height + rect1.y > rect2.y
            );
        }

        function Star(x, y) {
            var r = Math.max(50, Math.floor(Math.random() * 256));
            var g = Math.max(125, Math.floor(Math.random() * 256));
            var b = Math.max(240, Math.floor(Math.random() * 256));
            this.x = Math.floor(x);
            this.y = Math.floor(y);
            var size = Math.floor(Math.random() * Star.MAX_SIZE);
            this.width = size;
            this.height = size;
            this.variance = Math.max(Math.random(), .2);
            this.color = 'rgb(' + r + ', ' + g + ', ' + b + ')';
        }

        Star.SPEED = 5;
        Star.MAX_SIZE = 2;
        Star.prototype.update = function() {
            if (game.overdrive) {
                var travel = Star.SPEED * this.variance * 6;
                this.width = 50;
            } else {
                var travel = Star.SPEED * this.variance;
                this.width = this.height;
            }
            this.x -= travel;
            if (this.x + this.width < 0) {
                this.x = canvas.width;
            }
        }

        Star.prototype.render = function(context) {
            if (game.overdrive) {
                context.globalAlpha = .6;
            }
            context.fillStyle = (game.overdrive) ? 'rgba(125, 135, 255, 1)' : this.color;
            context.fillRect(this.x, this.y, this.width, this.height);
            context.globalAlpha = 1;
        }

        function Explosion(x, y) {
            this.currentFrame = 0;
            this.frames = 12;
            this.buffer = 4;
            this.currentBuffer = 0;
            this.alive = false;
            this.img = document.createElement('img');
            this.img.src = explosionSprite;
        }

        Explosion.prototype.reset = function() {
            this.currentFrame = 0;
            this.frames = 12;
            this.buffer = 4;
            this.currentBuffer = 0;
            this.alive = false;
        };

        Explosion.prototype.update = function() {
            if (!this.alive) return;
            this.x -= 2; 
            if (this.currentBuffer === this.buffer) {
                this.currentBuffer = 0;
                this.currentFrame++;
                if (this.currentFrame === this.frames) {
                    this.reset();
                }
            }
            this.currentBuffer++;
        }

        Explosion.prototype.render = function(context) {
            if (!this.alive) return;
            context.drawImage(
                this.img,
                0, this.currentFrame * 32, 32, 32,
                this.x - 16, this.y - 16, 64, 64
            );
        }

        function Ship(x, y, width, height, health) {
            this.x = x;
            this.y = y;
            this.width = width;
            this.height = height;
            this.health = health;
            this.hit = false;
            this.alive = true;
            this.vx = 0;
            this.vy = 0;
        }

        Ship.prototype.render = function(context) {
            context.fillStyle = '#666';
            context.fillRect(this.x, this.y, this.width, this.height);
        }

        Ship.prototype.takeDamage = function(damage) {
            this.health -= damage;
            if (this.health <= 0) {
                this.alive = false;
            }
        }

        function Bullet(x, y, dir, speed) {
            this.vx = 0;
            this.vy = 0;
            this.width = 16;
            this.height = 8;
            this.x = x;
            this.y = y;
            this.dir = dir;
            this.speed = speed;
            this.alive = false;
            this.img = document.createElement('img');
            this.img.src = bulletSprite;
        }

        Bullet.prototype.update = function() {
            if (!this.alive) return;
            if (this.dir === 1) this.vx = this.speed + (Math.min(game.currentState.player.powerLevel * 2, 20));
            if (this.dir === -1) this.vx = -this.speed;
            this.x += this.vx;
            if (this.x > canvas.width || this.x < -this.width) {
                this.alive = false;
            }
        }

        Bullet.prototype.render = function(context) {
            if (!this.alive) return;
            context.drawImage(this.img, 0, 0, 16, 8, this.x, this.y, this.width, this.height);
        }

        function BossBullet(x, y, targetX, targetY, speed) {
            this.x = x;
            this.y = y;
            this.width = 12;
            this.height = 12;
            this.speed = speed || 3;
            this.alive = true;

            var dx = targetX - x;
            var dy = targetY - y;
            var distance = Math.sqrt(dx * dx + dy * dy);
            this.vx = (dx / distance) * this.speed;
            this.vy = (dy / distance) * this.speed;
        }

        BossBullet.prototype.update = function() {
            if (!this.alive) return;
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < -this.width || this.x > canvas.width + this.width ||
                this.y < -this.height || this.y > canvas.height + this.height) {
                this.alive = false;
            }
        }

        BossBullet.prototype.render = function(context) {
            if (!this.alive) return;
            context.fillStyle = '#ff4444';
            context.fillRect(this.x, this.y, this.width, this.height);
            context.strokeStyle = '#ffffff';
            context.lineWidth = 1;
            context.strokeRect(this.x, this.y, this.width, this.height);
        }

        function PowerUp(x, y) {
            this.x = x;
            this.y = y;
            this.timer = Math.random() * 256;
            this.currentFrame = 0;
            this.currentBuffer = 0;
            this.buffer = 4;
            this.jump = canvas.height * .5;
            this.speed = 3;
            this.frames = 7;
            this.width = 16;
            this.height = 16;
            this.img = document.createElement('img');
            this.img.src = powerUpSprite;
            this.value = 20;
            this.alive = false;
        }

        PowerUp.prototype.update = function() {
            if (!this.alive) return;
            this.vy = Math.cos(this.timer) * this.jump;
            this.timer += .03;
            this.y = canvas.height * .5 + this.vy;
            this.x -= this.speed;
            if (this.x + this.width <= 0) {
                this.reset();
            }
        }

        PowerUp.prototype.reset = function() {
            this.alive = false;
        }

        PowerUp.prototype.render = function(context) {
            if (!this.alive) return;
            if (this.currentBuffer === this.buffer) {
                this.currentBuffer = 0;
                this.currentFrame++;
                if (this.currentFrame === this.frames) {
                    this.currentFrame = 0;
                }
            }
            this.currentBuffer++;
            context.drawImage(
                this.img, 0, this.currentFrame * 16, 16, 16,
                this.x, this.y, this.width, this.height
            );
        }

        function Player(x, y, health, weapon) {
            Ship.call(this, x, y, 32, 32, health);
            this.burning = false;
            this.frame = 0;
            this.burnFrame = 0;
            this.weapon = weapon;
            this.speed = 5;
            this.powerLevel = 1;
            this.bulletTimer = 5;
            this.bulletCoolDown = 5;
            this.img = document.createElement('img');
            this.burnImg = document.createElement('img');
            this.img.src = shipSprite;
            this.burnImg.src = burnSprite;
            this.bulletPool = [];
            this.hitBoxSize = [8, 8];
            this.maxHealth = health;
        }

        Player.prototype = new Ship();

        Player.prototype.getHitBox = function() {
            return {
                x: this.x + (this.width * .5) - (this.hitBoxSize[0] * .5),
                y: this.y + (this.height * .5) - (this.hitBoxSize[1] * .5),
                width: this.hitBoxSize[0],
                height: this.hitBoxSize[1],
            }
        }

        Player.prototype.update = function() {
            if (!this.alive) {
                if (inputManager.start) {
                    game.currentState.init();
                }
                return;
            }

            if (gameState.isMultiplayer && gameState.connected && gameState.socket) {

                gameState.socket.emit('playerInput', {
                    left: inputManager.leftPressed,
                    right: inputManager.rightPressed,
                    up: inputManager.upPressed,
                    down: inputManager.downPressed,
                    shoot: inputManager.shooting || game.autoShoot
                });

                if (inputManager.shooting || game.autoShoot) {
                    if (this.bulletCoolDown === this.bulletTimer) {
                        gameState.socket.emit('playerShoot', {});
                        this.bulletTimer = 0;
                    } else {
                        this.bulletTimer++;
                    }
                }

                this.burning = inputManager.rightPressed;
                return; 
            }

            this.vx = 0;
            this.vy = 0;

            if (inputManager.upPressed) {
                this.vy -= this.speed;
            }
            if (inputManager.downPressed) {
                this.vy += this.speed;
            }
            if (inputManager.rightPressed) {
                this.vx += this.speed;
                this.burning = true;
            } else {
                this.burning = false;
            }
            if (inputManager.leftPressed) {
                this.vx -= this.speed;
                this.burning = false;
            }

            if (inputManager.shooting || game.autoShoot) {
                if (this.bulletCoolDown === this.bulletTimer) {
                    this.shoot();
                    this.bulletTimer = 0;
                } else {
                    this.bulletTimer++;
                }
            }

            this.x += this.vx;
            this.y += this.vy;

            if (this.x < 0) this.x = 0;
            if (this.y < 0) this.y = 0;
            if (this.x + this.width > canvas.width) this.x = canvas.width - this.width;
            if (this.y + this.height > canvas.height) this.y = canvas.height - this.height;
        }

        Player.prototype.shoot = function() {
            if (this.powerLevel === 1) {
                var bullet = this.bulletPool.find(notAlive);
                if (!bullet) return;
                bullet.x = this.x + this.width - bullet.width;
                bullet.y = (this.y + (this.height * .5)) - (bullet.height * .5);
                bullet.alive = true;
            }

            if (this.powerLevel === 2) {
                var bullet = this.bulletPool.find(notAlive);
                if (!bullet) return;
                bullet.alive = true;

                var bullet2 = this.bulletPool.find(notAlive);
                if (!bullet2) return;
                bullet2.alive = true;

                bullet.x = this.x + this.width - bullet.width;
                bullet.y = (this.y + (this.height * .5)) - (bullet.height * .5) - 6;

                bullet2.x = this.x + this.width - bullet2.width;
                bullet2.y = (this.y + (this.height * .5)) - (bullet2.height * .5) + 6;
            }

            if (this.powerLevel >= 3) {
                var bullet = this.bulletPool.find(notAlive);
                if (!bullet) return;
                bullet.alive = true;

                var bullet2 = this.bulletPool.find(notAlive);
                if (!bullet2) return;
                bullet2.alive = true;

                var bullet3 = this.bulletPool.find(notAlive);
                if (!bullet3) return;
                bullet3.alive = true;

                bullet.x = this.x + this.width - bullet.width;
                bullet.y = (this.y + (this.height * .5)) - (bullet.height * .5) - 12;

                bullet2.x = this.x + this.width - bullet2.width + 8;
                bullet2.y = (this.y + (this.height * .5)) - (bullet2.height * .5);

                bullet3.x = this.x + this.width - bullet3.width;
                bullet3.y = (this.y + (this.height * .5)) - (bullet3.height * .5) + 12;
            }

            if (this.powerLevel >= 5) {
                var bullet = this.bulletPool.find(notAlive);
                if (!bullet) return;
                bullet.alive = true;

                var bullet2 = this.bulletPool.find(notAlive);
                if (!bullet2) return;
                bullet2.alive = true;

                bullet.x = this.x + this.width - bullet.width - 8;
                bullet.y = (this.y + (this.height * .5)) - (bullet.height * .5) - 24;
                bullet2.x = this.x + this.width - bullet2.width - 8;
                bullet2.y = (this.y + (this.height * .5)) - (bullet2.height * .5) + 24;
            }
        }

        Player.prototype.render = function(context) {
            if (!this.alive) return;

            this.buffer = this.buffer ? this.buffer + 1 : 1;
            if (this.buffer && this.buffer == 4) {
                this.frame += 1;
                if (this.frame >= 10) this.frame = 0;
                this.burnFrame += 1;
                if (this.burnFrame >= 2) this.burnFrame = 0;
                this.buffer = 0;
            }

            context.drawImage(
                this.img, 0, this.frame * 32, 32, 32,
                this.x, this.y, this.width, this.height
            );

            if (this.burning) {
                context.drawImage(
                    this.burnImg, 0, this.burnFrame * 32, 32, 32,
                    this.x, this.y, this.width, this.height
                );
            }
        }

        function Popcorn(x, y) {
            Ship.call(this, x, y, 32, 32, Popcorn.HEALTH);
            this.img = document.createElement('img');
            this.img.src = popCornSprite;
            this.frames = 12;
            this.buffer = 4;
            this.speed = Popcorn.SPEED;
            this.value = 5;
            this.healthMax = Popcorn.HEALTH;
            this.reset();
        }

        Popcorn.prototype = new Ship();
        Popcorn.SPEED = 5;
        Popcorn.HEALTH = 80;

        Popcorn.prototype.reset = function() {
            this.x = canvas.width;
            this.y = Math.random() * (canvas.height - this.height);
            this.currentFrame = 0;
            this.currentBuffer = 0;
            this.alive = false;
            this.health = Popcorn.HEALTH;
        }

        Popcorn.prototype.update = function() {
            if (!this.alive) return;
            this.vx = -this.speed;
            this.x += this.vx;
            if (this.x + this.width <= 0) {
                this.reset();
            }
        }

        Popcorn.prototype.render = function(context) {
            if (!this.alive) return;

            if (this.currentBuffer === this.buffer) {
                this.currentBuffer = 0;
                this.currentFrame++;
                if (this.currentFrame === this.frames) {
                    this.currentFrame = 0;
                }
            }

            context.drawImage(
                this.img, 0, this.currentFrame * 32, 32, 32,
                this.x, this.y, this.width, this.height
            );

            context.fillStyle = '#f00';
            context.fillRect(this.x, this.y - 2, this.width, 1);
            context.fillStyle = '#0f0';
            this.perc = this.health / this.healthMax;
            context.fillRect(this.x, this.y - 2, this.width * this.perc, 1);

            if (this.hit) {
                var tmpOperation = context.globalCompositeOperation;
                context.globalCompositeOperation = 'color-dodge';
                context.drawImage(
                    this.img, 0, this.currentFrame * 32, 32, 32,
                    this.x, this.y, this.width, this.height
                );
                context.globalCompositeOperation = tmpOperation;
                this.hit = false;
            }

            this.currentBuffer++;
        }

        function Boss(x, y) {
            Ship.call(this, x, y, 128, 96, Boss.HEALTH);
            this.maxHealth = Boss.HEALTH;
            this.speed = 2;
            this.shootTimer = 0;
            this.shootCooldown = 60;
            this.phase = 1;
            this.movePattern = 0;
            this.moveTimer = 0;
            this.bulletPool = [];
            this.value = 1000;
            this.name = "DESTROYER";

            for (var i = 0; i < 50; i++) {
                this.bulletPool.push(new BossBullet(0, 0, 0, 0, 0));
                this.bulletPool[i].alive = false;
            }

            this.img = document.createElement('img');
            this.img.src = popCornSprite;
            this.frames = 12;
            this.buffer = 2; 
            this.currentFrame = 0;
            this.currentBuffer = 0;
        }

        Boss.prototype = new Ship();
        Boss.HEALTH = 2000;

        Boss.prototype.update = function() {
            if (!this.alive) return;

            this.moveTimer++;
            this.shootTimer++;

            if (this.phase === 1) {

                if (this.moveTimer < 120) {
                    this.y -= this.speed;
                } else if (this.moveTimer < 240) {
                    this.y += this.speed;
                } else {
                    this.moveTimer = 0;
                }

                if (this.shootTimer >= this.shootCooldown) {
                    this.shootAtPlayer();
                    this.shootTimer = 0;
                }
            } else if (this.phase === 2) {

                this.shootCooldown = 30;

                if (this.moveTimer < 80) {
                    this.y -= this.speed * 1.5;
                } else if (this.moveTimer < 160) {
                    this.y += this.speed * 1.5;
                } else {
                    this.moveTimer = 0;
                }

                if (this.shootTimer >= this.shootCooldown) {
                    this.shootSpread();
                    this.shootTimer = 0;
                }
            } else if (this.phase === 3) {

                this.shootCooldown = 15;

                var centerY = canvas.height / 2;
                this.y = centerY + Math.sin(this.moveTimer * 0.1) * 100;

                if (this.shootTimer >= this.shootCooldown) {
                    this.shootBulletHell();
                    this.shootTimer = 0;
                }
            }

            if (this.y < 0) this.y = 0;
            if (this.y + this.height > canvas.height) this.y = canvas.height - this.height;

            this.bulletPool.forEach(function(bullet) {
                bullet.update();
            });

            var healthPercent = this.health / this.maxHealth;
            if (healthPercent < 0.66 && this.phase === 1) {
                this.phase = 2;
                console.log("Boss entered phase 2!");
            } else if (healthPercent < 0.33 && this.phase === 2) {
                this.phase = 3;
                console.log("Boss entered phase 3!");
            }

            if (this.currentBuffer === this.buffer) {
                this.currentBuffer = 0;
                this.currentFrame++;
                if (this.currentFrame === this.frames) {
                    this.currentFrame = 0;
                }
            }
            this.currentBuffer++;
        }

        Boss.prototype.shootAtPlayer = function() {
            if (!game.currentState.player || !game.currentState.player.alive) return;

            var bullet = this.bulletPool.find(notAlive);
            if (bullet) {
                bullet.x = this.x;
                bullet.y = this.y + this.height / 2;
                bullet.alive = true;

                var playerX = game.currentState.player.x + game.currentState.player.width / 2;
                var playerY = game.currentState.player.y + game.currentState.player.height / 2;

                var dx = playerX - bullet.x;
                var dy = playerY - bullet.y;
                var distance = Math.sqrt(dx * dx + dy * dy);

                bullet.vx = (dx / distance) * 4;
                bullet.vy = (dy / distance) * 4;
            }
        }

        Boss.prototype.shootSpread = function() {
            if (!game.currentState.player || !game.currentState.player.alive) return;

            for (var i = -1; i <= 1; i++) {
                var bullet = this.bulletPool.find(notAlive);
                if (bullet) {
                    bullet.x = this.x;
                    bullet.y = this.y + this.height / 2;
                    bullet.alive = true;

                    var playerX = game.currentState.player.x + game.currentState.player.width / 2;
                    var playerY = game.currentState.player.y + game.currentState.player.height / 2;

                    var dx = playerX - bullet.x;
                    var dy = playerY - bullet.y;
                    var distance = Math.sqrt(dx * dx + dy * dy);

                    var angle = Math.atan2(dy, dx) + (i * 0.3);
                    bullet.vx = Math.cos(angle) * 4;
                    bullet.vy = Math.sin(angle) * 4;
                }
            }
        }

        Boss.prototype.shootBulletHell = function() {

            for (var i = 0; i < 8; i++) {
                var bullet = this.bulletPool.find(notAlive);
                if (bullet) {
                    bullet.x = this.x + this.width / 2;
                    bullet.y = this.y + this.height / 2;
                    bullet.alive = true;

                    var angle = (i / 8) * Math.PI * 2;
                    bullet.vx = Math.cos(angle) * 3;
                    bullet.vy = Math.sin(angle) * 3;
                }
            }
        }

        Boss.prototype.takeDamage = function(damage) {
            this.health -= damage;
            this.hit = true;
            if (this.health <= 0) {
                this.alive = false;
                game.score += this.value;
                game.updateScore();

                document.getElementById('boss-health').style.display = 'none';
                document.getElementById('boss-name').style.display = 'none';
            } else {

                var healthPercent = this.health / this.maxHealth;
                document.getElementById('boss-health-bar').style.width = (healthPercent * 100) + '%';
            }
        }

        Boss.prototype.render = function(context) {
            if (!this.alive) return;

            context.drawImage(
                this.img, 0, this.currentFrame * 32, 32, 32,
                this.x, this.y, this.width, this.height
            );

            context.fillStyle = '#f00';
            context.fillRect(this.x, this.y - 10, this.width, 4);
            context.fillStyle = '#0f0';
            var healthPercent = this.health / this.maxHealth;
            context.fillRect(this.x, this.y - 10, this.width * healthPercent, 4);

            context.fillStyle = '#ffffff';
            context.font = '16px arial';
            context.textAlign = 'center';
            context.fillText(this.name, this.x + this.width / 2, this.y - 15);
            context.textAlign = 'left';

            if (this.hit) {
                var tmpOperation = context.globalCompositeOperation;
                context.globalCompositeOperation = 'color-dodge';
                context.drawImage(
                    this.img, 0, this.currentFrame * 32, 32, 32,
                    this.x, this.y, this.width, this.height
                );
                context.globalCompositeOperation = tmpOperation;
                this.hit = false;
            }

            this.bulletPool.forEach(function(bullet) {
                bullet.render(context);
            });
        }

        function TitleState(name) {
            State.call(this, name, this.update, this.render);
        }

        TitleState.prototype = new State();

        TitleState.prototype.init = function() {
            game.overdrive = true;
            context.setTransform(1, 0, 0, 1, 0, 0);
            game.showUI('title');
            this.entities = [];
            this.starField = [];
            for (var i = 0; i < 1024; i++) {
                this.starField.push(
                    new Star(
                        Math.random() * canvas.width,
                        Math.random() * canvas.height
                    )
                );
            }
        }

        TitleState.prototype.update = function() {
            if (inputManager.start) {
                game.setState(game.states.game);
                game.currentState.init();
            }
            if (inputManager.multiplayer) {
                inputManager.multiplayer = false; 
                startMultiplayer();
            }
            this.starField.forEach(function(entity) {
                entity.update();
            });
        }

        TitleState.prototype.render = function(context) {
            context.clearRect(0, 0, canvas.width, canvas.height);
            this.starField.forEach(function(entity) {
                entity.render(context);
            });
        }

        function GameOverState(name) {
            State.call(this, name, this.update, this.render);
        }

        GameOverState.prototype = new State();

        GameOverState.prototype.init = function() {
            context.setTransform(1, 0, 0, 1, 0, 0);
            this.timer = 0;
            console.log('Game Over');
            game.showUI('game_over');
            document.querySelector('#final_score').innerHTML = 'FINAL SCORE: ' + game.score;

            document.getElementById('boss-health').style.display = 'none';
            document.getElementById('boss-name').style.display = 'none';
        }

        GameOverState.prototype.update = function() {
            if (inputManager.start) {
                game.setState(game.states.game);
                game.currentState.init();
                game.reset();
            }
            this.timer++;
        }

        GameOverState.prototype.render = function(context) {
            for (var i = 0; i < canvas.width; i++) {
                context.drawImage(
                    canvas,
                    i, 0, 1, canvas.height,
                    i, Math.sin((i * 20 * Math.PI / 180)) * 2, 1, canvas.height
                );
            }
            if (this.timer > 60) {
                context.globalAlpha = .3;
            }
        }

        function GameState(name) {
            State.call(this, name, this.update, this.render);
        }

        GameState.prototype = new State();

        GameState.prototype.init = function() {

            if (!gameState.isMultiplayer) {
                game.overdrive = true;
                this.overdriveTimer = 90;
            } else {
                game.overdrive = false;
                this.overdriveTimer = 0;
            }

            context.setTransform(1, 0, 0, 1, 0, 0);
            game.showUI('game');
            this.timer = 0;
            this.tier1 = 1 * WAVE;
            this.tier2 = 2 * WAVE;
            this.tier3 = 3 * WAVE;
            this.tier4 = 4 * WAVE;
            this.bossWave = 5 * WAVE; 
            this.enemyTimerEasy = 120;
            this.enemyTimerMedium = 60;
            this.enemyTimerHard = 30;
            this.enemyTimerNightmare = 5;
            this.currentEnemyTimer = this.enemyTimerEasy;
            this.powerUpTimer = 1600;
            this.bossSpawned = false;
            this.otherPlayers = []; 

            document.getElementById('boss-health').style.display = 'none';
            document.getElementById('boss-name').style.display = 'none';

            this.starField = [];
            for (var i = 0; i < 1024; i++) {
                this.starField.push(
                    new Star(
                        Math.random() * canvas.width,
                        Math.random() * canvas.height
                    )
                );
            }

            this.player = new Player(20, Math.floor(canvas.height * .5), 100, null);
            for (var i = 0; i < 256; i++) {
                this.player.bulletPool.push(new Bullet(this.player.x + 32, this.player.y + 16, 1, 15));
            }

            this.enemyList = [];
            for (var i = 0; i < 32; i++) {
                this.enemyList.push(new Popcorn(canvas.width, Math.random() * (canvas.height - 32)));
            }

            this.explosions = [];
            for (var i = 0; i < 32; i++) {
                this.explosions.push(new Explosion(0, 0));
            }

            this.powerUps = [];
            for (var i = 0; i < 32; i++) {
                this.powerUps.push(new PowerUp(0, 0));
            }

            this.boss = null;

            this.entities = [this.player];
            this.entities = this.entities.concat(
                this.enemyList,
                this.explosions,
                this.powerUps,
                this.player.bulletPool
            );

            console.log('game initialised');
        }

        GameState.prototype.deployEnemies = function() {

            if (this.boss && this.boss.alive) return;

            if (this.timer && (this.timer % this.currentEnemyTimer === 0)) {
                var enemy = this.enemyList.find(function(enemy) {
                    return !enemy.alive;
                });
                if (enemy) {
                    enemy.reset();
                    enemy.x = canvas.width;
                    enemy.alive = true;
                    enemy.y = Math.max(4, (canvas.height * Math.random()) - enemy.height);
                }
            }
        }

        GameState.prototype.deployPowerUps = function() {
            if (this.timer && (this.timer % this.powerUpTimer === 0)) {
                if (Math.random() >= .01) {
                    var powerup = this.powerUps.find(function(powerup) {
                        return !powerup.alive;
                    });
                    if (powerup) {
                        powerup.x = canvas.width;
                        powerup.alive = true;
                        powerup.y = Math.random() * (canvas.height - powerup.height);
                    }
                }
            }
        }

        GameState.prototype.spawnBoss = function() {
            if (!this.bossSpawned && this.timer > this.bossWave) {
                this.boss = new Boss(canvas.width - 150, canvas.height / 2 - 48);
                this.bossSpawned = true;

                document.getElementById('boss-health').style.display = 'block';
                document.getElementById('boss-name').style.display = 'block';
                document.getElementById('boss-name').textContent = this.boss.name;
                document.getElementById('boss-health-bar').style.width = '100%';

                console.log('Boss spawned!');
            }
        }

        GameState.prototype.update = function() {

            if (gameState.isMultiplayer) {

                game.overdrive = false;

                if (this.player) {

                    this.player.update();
                }

                this.entities.forEach(function(entity) {
                    if (entity.constructor.name === 'Explosion') {
                        entity.update();
                    }
                });

                if (this.boss) {

                    if (this.boss.currentBuffer === this.boss.buffer) {
                        this.boss.currentBuffer = 0;
                        this.boss.currentFrame++;
                        if (this.boss.currentFrame === this.boss.frames) {
                            this.boss.currentFrame = 0;
                        }
                    }
                    this.boss.currentBuffer++;
                }
                return; 
            }

            if (this.timer > this.tier2) {
                this.currentEnemyTimer = this.enemyTimerMedium;
            }
            if (this.timer > this.tier3) {
                this.currentEnemyTimer = this.enemyTimerHard;
            }
            if (this.timer > this.tier4) {
                this.currentEnemyTimer = this.enemyTimerNightmare;
            }

            if (this.overdriveTimer < this.timer) {
                game.overdrive = false;
            }
            this.timer++;

            this.deployEnemies();
            this.deployPowerUps();
            this.spawnBoss();

            this.entities.forEach(function(entity) {
    entity.update();
});

if (this.boss) {
    this.boss.update();
}

this.player.bulletPool.forEach(function(bullet) {
    if (!bullet.alive) return;

    game.currentState.enemyList.forEach(function(enemy) {
        if (!enemy.alive) return;
        if (Intersection.rectanglesIntersect(bullet, enemy)) {
            enemy.takeDamage(10);
            bullet.alive = false;
            if (!enemy.alive) {
                game.score += enemy.value;
                game.kills++;
                game.updateScore();
                game.updateKills();
                enemy.hit = true;
                var explosion = game.currentState.explosions.find(notAlive);
                if (explosion) {
                    explosion.x = enemy.x;
                    explosion.y = enemy.y;
                    explosion.alive = true;
                }
            }
        }
    });

    if (game.currentState.boss && game.currentState.boss.alive) {
        if (Intersection.rectanglesIntersect(bullet, game.currentState.boss)) {
            game.currentState.boss.takeDamage(10);
            bullet.alive = false;
            if (!game.currentState.boss.alive) {
                game.kills++;
                game.updateKills();
                var explosion = game.currentState.explosions.find(notAlive);
                if (explosion) {
                    explosion.x = game.currentState.boss.x + game.currentState.boss.width / 2;
                    explosion.y = game.currentState.boss.y + game.currentState.boss.height / 2;
                    explosion.alive = true;
                }
            }
        }
    }
});

var player = this.player;
if (player.alive) {

    this.enemyList.forEach(function(enemy) {
        if (!enemy.alive) return;
        var playerHitBox = player.getHitBox();
        if (Intersection.rectanglesIntersect(enemy, playerHitBox)) {
            player.takeDamage(500);
            enemy.takeDamage(500);
            game.lives--;
            game.updateLives();
            var explosion = game.currentState.explosions.find(notAlive);
            if (explosion) {
                explosion.x = enemy.x;
                explosion.y = enemy.y;
                explosion.alive = true;
            }

            var explosion2 = game.currentState.explosions.find(notAlive);
            if (explosion2) {
                explosion2.x = player.x;
                explosion2.y = player.y;
                explosion2.alive = true;
            }

            if (game.lives === 0) {
                game.setState(game.states.game_over);
                game.currentState.init();
            }
        }
    });

    if (this.boss && this.boss.alive) {
        var playerHitBox = player.getHitBox();
        this.boss.bulletPool.forEach(function(bullet) {
            if (!bullet.alive) return;
            if (Intersection.rectanglesIntersect(bullet, playerHitBox)) {
                player.takeDamage(25);
                bullet.alive = false;
                game.lives--;
                game.updateLives();

                var explosion = game.currentState.explosions.find(notAlive);
                if (explosion) {
                    explosion.x = player.x;
                    explosion.y = player.y;
                    explosion.alive = true;
                }

                if (game.lives === 0) {
                    game.setState(game.states.game_over);
                    game.currentState.init();
                }
            }
        });

        if (Intersection.rectanglesIntersect(this.boss, playerHitBox)) {
            player.takeDamage(500);
            this.boss.takeDamage(100);
            game.lives--;
            game.updateLives();

            var explosion = game.currentState.explosions.find(notAlive);
            if (explosion) {
                explosion.x = player.x;
                explosion.y = player.y;
                explosion.alive = true;
            }

            if (game.lives === 0) {
                game.setState(game.states.game_over);
                game.currentState.init();
            }
        }
    }

    this.powerUps.forEach(function(powerup) {
        if (!powerup.alive) return;
        if (Intersection.rectanglesIntersect(powerup, player.getHitBox())) {
            player.powerLevel++;
            powerup.reset();
            game.score += powerup.value;
            game.updateScore();
        }
    });
}
        }
GameState.prototype.renderBackground = function(context) {
    this.starField.forEach(function(star) {
        star.update();
        star.render(context);
    });
};

        GameState.prototype.render = function(context) {
            context.fillStyle = '#000';
            context.fillRect(0, 0, canvas.width, canvas.height);
            context.globalAlpha = 1;
            this.renderBackground(context);

            this.entities.forEach(function(entity) {
                if (entity.constructor.name !== 'Player') {
                    entity.render(context);
                }
            });

            if (this.player) {
                this.player.render(context);
            }

            if (gameState.isMultiplayer && this.otherPlayers) {
                this.otherPlayers.forEach(function(otherPlayer) {
                    if (otherPlayer.alive) {

                        otherPlayer.buffer = otherPlayer.buffer ? otherPlayer.buffer + 1 : 1;
                        if (otherPlayer.buffer && otherPlayer.buffer == 4) {
                            otherPlayer.frame = (otherPlayer.frame || 0) + 1;
                            if (otherPlayer.frame >= 10) otherPlayer.frame = 0;
                            otherPlayer.buffer = 0;
                        }

                        context.drawImage(
                            otherPlayer.img, 0, (otherPlayer.frame || 0) * 32, 32, 32,
                            otherPlayer.x, otherPlayer.y, 32, 32  
                        );

                        context.fillStyle = '#00aaff';
                        context.font = '14px arial';
                        context.textAlign = 'center';
                        context.fillText(otherPlayer.name || 'Unknown', otherPlayer.x + 16, otherPlayer.y - 8);
                        context.textAlign = 'left';

                        if (otherPlayer.health < (otherPlayer.max_health || 100)) {
                            var healthPercent = otherPlayer.health / (otherPlayer.max_health || 100);
                            context.fillStyle = '#ff0000';
                            context.fillRect(otherPlayer.x, otherPlayer.y - 15, 32, 3);
                            context.fillStyle = '#00ff00';
                            context.fillRect(otherPlayer.x, otherPlayer.y - 15, 32 * healthPercent, 3);
                        }
                    }
                });
            }

            if (this.boss) {
                this.boss.render(context);
            }

            if (gameState.isMultiplayer) {
                context.fillStyle = '#00ff00';
                context.font = '16px arial';
                context.textAlign = 'left';
                context.fillText('Room: ' + (gameState.roomId || 'None'), 10, canvas.height - 40);
                context.fillText('Player ID: ' + (gameState.playerId || 'None'), 10, canvas.height - 20);
                context.fillText('Mode: Multiplayer', 10, canvas.height - 60);
                if (this.otherPlayers) {
                    context.fillText('Other Players: ' + this.otherPlayers.length, 10, canvas.height - 80);
                }
            } else {
                context.fillStyle = '#00ff00';
                context.font = '16px arial';
                context.textAlign = 'left';
                context.fillText('Mode: Single Player', 10, canvas.height - 20);
            }
        }

        function notAlive(item) {
            return !item.alive;
        }

        function alive(item) {
            return item.alive;
        }

        function Game() {
            this.reset();
            this.states = {};
            this.states['game'] = new GameState('game');
            this.states['title'] = new TitleState('title');
            this.states['game_over'] = new GameOverState('game_over');
            this.entities = [];
        }

        Game.prototype.reset = function() {
            this.score = 0;
            this.lives = 3;
            this.kills = 0;
            this.updateScore();
            this.updateLives();
            this.updateKills();
        }

        Game.prototype.setState = function(state) {
            this.currentState = state;
        }

        Game.prototype.showUI = function(name) {

            document.querySelectorAll('.state-ui-container').forEach(function(element) {
                element.style.display = 'none';
            });

            var targetElement = document.querySelector('#' + name);
            if (targetElement) {
                targetElement.style.display = 'flex';
            }

            console.log('Showing UI:', name);
        }

        Game.prototype.updateScore = function() {
            document.getElementById('score').innerHTML = 'SCORE: ' + this.score;
        }

        Game.prototype.updateLives = function() {
            document.getElementById('lives').innerHTML = 'LIVES: ' + this.lives;
        }

        Game.prototype.updateKills = function() {
            var killsEl = document.getElementById('kills');
            if (killsEl) {
                killsEl.innerHTML = 'KILLS: ' + this.kills;
            }
        }

        Game.prototype.updateTeammateStatus = function() {
            var statusEl = document.getElementById('teammate-status');
            if (statusEl && gameState.isMultiplayer && game.currentState.otherPlayers) {
                var deadTeammates = game.currentState.otherPlayers.filter(function(p) { return !p.alive; });
                if (deadTeammates.length > 0) {
                    statusEl.innerHTML = 'PRESS [R] TO REVIVE TEAMMATE (500 pts)';
                    statusEl.style.display = 'block';
                } else {
                    statusEl.style.display = 'none';
                }
            } else if (statusEl) {
                statusEl.style.display = 'none';
            }
        }

        Game.prototype.update = function() {
            this.currentState.update();
        }

        Game.prototype.render = function(context) {
            this.currentState.render(context);
        }

        Game.prototype.loop = function() {
            window.requestAnimationFrame(function() { this.loop() }.bind(this));
            var now = Date.now();
            var dt = now - then;
            if (dt <= fps) return;
            then = now - (dt % fps);
            this.update();
            this.render(context);
        }

        Game.prototype.init = function() {
            this.autoShoot = true;
            this.setState(this.states.title);
            this.currentState.init();
            window.requestAnimationFrame(function() { this.loop() }.bind(this));
        }

        function InputManager() {
            this.upPressed = false;
            this.downPressed = false;
            this.leftPressed = false;
            this.rightPressed = false;
            this.shooting = false;
            this.start = false;
            this.multiplayer = false;
        }

        InputManager.prototype.handleKey = function(e, state) {
            switch (e.keyCode) {
                case UP:
                    this.upPressed = state;
                    break;
                case DOWN:
                    this.downPressed = state;
                    break;
                case LEFT:
                    this.leftPressed = state;
                    break;
                case RIGHT:
                    this.rightPressed = state;
                    break;
                case SHOOT:
                    this.shooting = state;
                    break;
                case RESET:
                    if (state && game.currentState.name === 'title') {

                        game.reset();
                        game.setState(game.states.title);
                        game.currentState.init();
                    } else if (state && game.currentState.name === 'game' && gameState.isMultiplayer) {

                        this.reviveTeammate();
                    }
                    break;
                case START:
                    this.start = state;
                    break;
                case MULTIPLAYER:

                    if (state && !gameState.isMultiplayer) {
                        this.multiplayer = true;
                    }
                    break;
                case ESCAPE:
                    if (state) {
                        game.setState(game.states.title);
                        game.currentState.init();
                        if (gameState.socket) {
                            gameState.socket.disconnect();
                            gameState.isMultiplayer = false;
                        }
                    }
                    break;
            }
        };

        InputManager.prototype.reviveTeammate = function() {
            if (!gameState.isMultiplayer || !gameState.connected || !gameState.socket) return;

            if (game.score >= 500) {
                game.score -= 500;
                game.updateScore();
                gameState.socket.emit('reviveTeammate', {});
                console.log('Revive teammate request sent');
            } else {
                console.log('Not enough points to revive teammate (need 500)');
            }
        };

        function connectToServer() {
            return new Promise((resolve, reject) => {
                if (typeof io === 'undefined') {
                    reject('Socket.io not available');
                    return;
                }

                gameState.socket = io('http://http://jha.jpoop.in:80');

                gameState.socket.on('connect', () => {
                    console.log('✅ Connected to server');
                    gameState.connected = true;
                    updateConnectionStatus(true);
                    resolve();
                });

                gameState.socket.on('disconnect', () => {
                    console.log('❌ Disconnected from server');
                    gameState.connected = false;
                    updateConnectionStatus(false);
                });

                gameState.socket.on('connect_error', (error) => {
                    console.error('❌ Connection failed:', error);
                    reject('Connection failed');
                });

                gameState.socket.on('joinedGame', (data) => {
                    if (data.success) {
                        gameState.playerId = data.playerId;
                        gameState.roomId = data.roomId;
                        console.log(`🎮 Joined room ${data.roomId} as ${data.playerName}`);
                        game.setState(game.states.game);
                        game.currentState.init();
                    }
                });

                gameState.socket.on('reviveResponse', (data) => {
                    if (data.success) {
                        console.log('Teammate revived successfully');
                    } else {
                        console.log('Revive failed:', data.message);
                    }
                });
                gameState.socket.on('reviveResponse', (data) => {
                    if (data.success) {
                        console.log('Teammate revived successfully');
                    } else {
                        console.log('Revive failed:', data.message);
                    }
                });

                gameState.socket.on('reviveResponse', (data) => {
                    if (data.success) {
                        console.log('Teammate revived successfully');
                    } else {
                        console.log('Revive failed:', data.message);
                    }
                });

                gameState.socket.on('gameState', (data) => {

                    if (gameState.isMultiplayer && game.currentState.name === 'game') {

                        game.currentState.enemyList.forEach(enemy => enemy.alive = false);
                        game.currentState.player.bulletPool.forEach(bullet => bullet.alive = false);
                        game.currentState.otherPlayers = [];

                        if (data.players) {
                            data.players.forEach(serverPlayer => {
                                if (serverPlayer.id === gameState.playerId) {

                                    if (game.currentState.player) {
                                        game.currentState.player.x = serverPlayer.x;
                                        game.currentState.player.y = serverPlayer.y;
                                        game.currentState.player.health = serverPlayer.health;
                                        game.currentState.player.alive = serverPlayer.alive;

                                        if (serverPlayer.score !== undefined) {
                                            game.score = serverPlayer.score;
                                            game.updateScore();
                                        }
                                    }
                                } else {

                                    var otherPlayer = {
                                        id: serverPlayer.id,
                                        name: serverPlayer.name,
                                        x: serverPlayer.x,
                                        y: serverPlayer.y,
                                        width: serverPlayer.width || 32,
                                        height: serverPlayer.height || 32,
                                        health: serverPlayer.health,
                                        max_health: serverPlayer.max_health || 100,
                                        alive: serverPlayer.alive,
                                        score: serverPlayer.score || 0,
                                        img: document.createElement('img')
                                    };
                                    otherPlayer.img.src = shipSprite;
                                    game.currentState.otherPlayers.push(otherPlayer);
                                }
                            });
                        }

                        if (data.enemies) {
                            data.enemies.forEach((serverEnemy, index) => {
                                if (index < game.currentState.enemyList.length) {
                                    let enemy = game.currentState.enemyList[index];
                                    enemy.x = serverEnemy.x;
                                    enemy.y = serverEnemy.y;
                                    enemy.health = serverEnemy.health;
                                    enemy.alive = serverEnemy.alive;
                                    enemy.width = serverEnemy.width;
                                    enemy.height = serverEnemy.height;
                                }
                            });
                        }

                        if (data.bullets) {
                            data.bullets.forEach((serverBullet, index) => {
                                if (index < game.currentState.player.bulletPool.length) {
                                    let bullet = game.currentState.player.bulletPool[index];
                                    bullet.x = serverBullet.x;
                                    bullet.y = serverBullet.y;
                                    bullet.alive = serverBullet.alive;
                                    bullet.width = serverBullet.width || 16;
                                    bullet.height = serverBullet.height || 8;
                                }
                            });
                        }

                        game.updateTeammateStatus();
                    }
                });
            });
        }

        function updateConnectionStatus(connected) {
            const statusEl = document.getElementById('connection-status');
            statusEl.textContent = connected ? 'Online' : 'Offline';
            statusEl.className = 'connection-status ' + (connected ? 'connected' : 'disconnected');
        }

        async function startMultiplayer() {
            try {
                gameState.isMultiplayer = true;
                await connectToServer();

                const playerName = prompt('Enter your name:') || 'Player';
                const roomId = prompt('Enter room ID (or leave blank for "room1"):') || 'room1';

                gameState.socket.emit('joinGame', {
                    playerName: playerName,
                    roomId: roomId
                });
            } catch (error) {
                alert('Could not connect to server! Starting single player...');
                gameState.isMultiplayer = false;
                game.setState(game.states.game);
                game.currentState.init();
            }
        }

        var game = new Game();
        var inputManager = new InputManager();

        window.addEventListener('keydown', function(e) {
            game.autoShoot = false;
            inputManager.handleKey(e, true);
        });

        window.addEventListener('keyup', function(e) {
            inputManager.handleKey(e, false);
        });

        game.init();
