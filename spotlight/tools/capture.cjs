// npm install --no-save jsnes@3.0.0 (Node 22+)
const fs = require('node:fs'), path = require('node:path');
const {NES} = require(process.env.JSNES_PATH || 'jsnes');
const [rom, out] = process.argv.slice(2);
fs.mkdirSync(out,{recursive:true});
let pixels;
const nes = new NES({onFrame: f => pixels=f});
nes.loadROM(fs.readFileSync(rom,'binary'));
for(let i=1;i<=1150;i++) {
  nes.frame();
  const rgb=Buffer.alloc(256*240*3);
  pixels.forEach((c,j)=>{rgb[j*3]=c; rgb[j*3+1]=c>>8; rgb[j*3+2]=c>>16;});
  fs.writeFileSync(path.join(out,'f'+i),rgb);
}
